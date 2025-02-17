import datetime
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import BadHeaderError
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.api.v2.invoice.serializers import InvoiceSerializer
from mysite.gi.models import Invoice, InvoiceHistory, InvoiceTransaction
from mysite.order.models import Order
from mysite.order.templatetags.order_tags import calculate_total_amount_due, calculate_total_paid, \
    calculate_remaining_invoice_due
from .services.email_service import InvoiceEmailService
from .services.invoice_detail_service import DetailedInvoiceService
from .services.invoice_payment_service import InvoicePaymentService
from .services.invoice_services import InvoiceService, DeleteInvoiceService
from .services.invoice_list_service import ListInvoiceService
from ..estimator.serializers import EmailSerializer
from ..order.serializers import OrderSerializer

logger = logging.getLogger(__name__)


class InvoiceListView(APIView):
    """
    API view for managing and retrieving invoice-related data.

    Permissions:
        - Only authenticated users can access this view.

    Attributes:
        permission_classes (list): Restricts access to authenticated users (`IsAuthenticated`).

    Methods:
        post(request):
            Sends an email containing an invoice.

        get(request):
            Filters and lists invoices based on various criteria, with support for pagination.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Sends an invoice email to the specified recipient.

        Parameters:
            request (Request): HTTP request containing the email details in the following format:
                - `email_id` (int): ID of the invoice to be sent.
                - `to_email` (str): Recipient's email address.
                - `cc` (str, optional): CC email address(es). Default is an empty string.
                - `subject` (str): Email subject.

        Returns:
            Response:
                - HTTP 200: On successful email dispatch.
                - HTTP 400: If email sending fails or data is invalid.

        Example Request Body:
            {
                "email_id": 123,
                "to_email": "example@domain.com",
                "cc": "cc@domain.com",
                "subject": "Invoice #123"
            }
        """
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            invoice_id = serializer.validated_data['email_id']
            to_email = serializer.validated_data['to_email']
            cc = serializer.validated_data.get('cc', '')
            subject = serializer.validated_data['subject']

            success = InvoiceEmailService.send_invoice_email(invoice_id, to_email, cc, subject)
            if success:
                return Response({"message": "Invoice sent successfully!"}, status=status.HTTP_200_OK)

            return Response({"error": "Failed to send invoice."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Retrieves a filtered and paginated list of invoices based on query parameters.

        Query Parameters:
            - `search` (str, optional): Search term for filtering by project name or project number.
            - `paginate_by` (int, optional): Number of records per page. Defaults to `settings.PAGE_SIZE`.
            - `ordering` (str, optional): Field for sorting results. Default is `-created_on`.
            - `fromDate` (str, optional): Start date for filtering invoices (`MM/DD/YYYY` format).
            - `toDate` (str, optional): End date for filtering invoices (`MM/DD/YYYY` format).
            - `type` (str, optional): Invoice status filter. Options:
                - `fully-paid`
                - `partial-paid`
                - `not-paid`
                - `old-estimate`
            - `overdue` (bool, optional): Filter for overdue invoices. Pass `1` for true. Default is false.

        Returns:
            Response:
                - HTTP 200: On successful filtering and pagination.
                - Contains filtered invoices, pagination details, overdue settings, and result status.

        Example Response:
            {
                "invoices": [...],
                "pagination": {
                    "total_rows": 50,
                    "total_pages": 5,
                    "current_page": 1,
                    "page_size": 10
                },
                "overdue_days": 30,
                "overdue_result": true
            }
        """
        search = request.GET.get('search', '')
        paginate_by = int(request.GET.get('paginate_by', settings.PAGE_SIZE))
        ordering = request.GET.get('ordering', '-created_on')
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')
        invoice_type = request.GET.get('type')  # e.g., 'fully-paid', 'partial-paid', 'not-paid', 'old-estimate'
        overdue = request.GET.get('overdue', '0') == '1'

        # Fetch filtered invoices
        invoices = ListInvoiceService.filter_invoices(
            search=search,
            from_date=from_date,
            to_date=to_date,
            ordering=ordering,
            invoice_type=invoice_type,
            overdue=overdue,
        )

        # Paginate the filtered results
        paginator = Paginator(object_list=invoices, per_page=paginate_by)
        page_number = request.GET.get('page', 1)
        paginated_invoices = paginator.get_page(number=page_number)

        # Serialize and return response
        serializer = InvoiceSerializer(paginated_invoices, many=True)
        overdue_days = ListInvoiceService.get_overdue_days()

        return Response({
            'invoices': serializer.data,
            'pagination': {
                'total_rows': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': paginated_invoices.number,
                'page_size': paginate_by,
            },
            'overdue_days': overdue_days,
            'overdue_result': overdue
        }, status=status.HTTP_200_OK)


class InvoiceOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve non-archived and unassociated orders",
        operation_description=(
                "This endpoint retrieves orders that are not archived and not associated with any invoice."
        ),
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_QUERY,
                description="Filter order by ID (optional)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of available orders",
                schema=OrderSerializer(many=True),
            ),
            401: "Unauthorized - User must be authenticated",
        },
    )
    def get(self, request, order_id=None):
        """
        Retrieves available orders that are not archived or associated with a invoice.

        Returns:
            - Response: Serialized data of orders.
        """
        try:
            orders = (
                Order.objects.filter(archive=False)
                    .exclude(id__in=Invoice.objects.values_list("order_id", flat=True))
                    .order_by("-created_on")
            )

            if order_id:
                orders = orders.filter(id=order_id)

            if orders.count() == 0:
                return Response(
                    {"detail": "No orders available."},
                    status=status.HTTP_200_OK,
                )

            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "detail": "An error occurred while retrieving orders.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InvoiceCreateView(APIView):
    """
    Handles the creation of invoices.
    """
    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        operation_summary="Create a new invoice",
        operation_description="This endpoint creates a new invoice for a specific order.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "order_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the order for which the invoice is being created",
                ),
                "invoice_type": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Invoice type number",
                ),
                "date_started": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="date",
                    description="Start date of the invoice",
                ),
                "date_completed": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="date",
                    description="Completion date of the invoice",
                ),
                "terms": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Terms and conditions for the invoice",
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Description of the invoice",
                ),
                "percent_of_performance_completed": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format="float",
                    description="Percentage of performance completed",
                ),
                "attention": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Attention notes",
                ),
            },
            required=["order_id", "invoice_type", "date_started", "date_completed", "terms", "description"],
        ),
        responses={
            201: openapi.Response(
                description="Invoice successfully created",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "invoice_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="ID of the created invoice",
                        ),
                    },
                ),
            ),
            400: "Bad request - Validation failed",
            401: "Unauthorized - User must be authenticated",
            404: "Order not found",
        },
    )
    def post(self, request):
        """
        Create a new invoice for a specific order.
        """
        order_id = request.data.get('order_id')
        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        serializer = InvoiceSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            invoice = InvoiceService.create_invoice(
                validated_data=serializer.validated_data,
                request_user=request.user,
            )
            return Response(
                {
                    'invoice_id': invoice.id,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceUpdateView(APIView):
    """
    API View for updating an Invoice.

    Methods:
        - GET: Retrieve an existing invoice by ID.
        - PUT: Fully update an invoice with new data.
        - PATCH: Partially update an invoice with new data.

    Permissions:
        - Requires authentication (`IsAuthenticated`).
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, invoice_id):
        """
        Fully update an invoice.

        Args:
            request (Request): The incoming HTTP request.
            invoice_id (int): The ID of the invoice to update.

        Returns:
            Response: Updated invoice data or validation errors.
        """
        invoice = get_object_or_404(
            Invoice,
            id=invoice_id,
            is_deleted=False,

        )
        serializer = InvoiceSerializer(invoice, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_invoice = InvoiceService.update_invoice(invoice, serializer.validated_data, request)
            return Response(InvoiceSerializer(updated_invoice).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, invoice_id):
        """
        Partially update an invoice.

        Args:
            request (Request): The incoming HTTP request.
            invoice_id (int): The ID of the invoice to update.

        Returns:
            Response: Updated invoice data or validation errors.
        """
        invoice = get_object_or_404(
            Invoice,
            id=invoice_id,
            is_deleted=False,

        )
        serializer = InvoiceSerializer(invoice, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_invoice = InvoiceService.update_invoice(invoice, serializer.validated_data, request)
            return Response(InvoiceSerializer(updated_invoice).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(APIView):
    """
    API View for retrieving and processing invoice details.

    Methods:
        - GET: Retrieves the invoice details and processes the invoice if no history exists.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        """
        Retrieves the details of the specified invoice and processes it if necessary.

        Args:
            request (Request): The incoming HTTP request.
            invoice_id (int): The ID of the invoice to retrieve.

        Returns:
            Response: The invoice details or a 404 error if not found.
        """
        # Retrieve the invoice
        invoice = get_object_or_404(
            Invoice,
            id=invoice_id,
            is_deleted=False,

        )

        try:
            data = DetailedInvoiceService.process_invoice(
                invoice=invoice,
                user=request.user,
            )
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error processing invoice {invoice_id}: {str(e)}"
            )
            return Response(
                {"error": "An error occurred while processing the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InvoiceDeleteView(APIView):
    """
    View for deleting an invoice. Only authenticated users can access this view.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, invoice_id):
        """
        Handle the DELETE request to remove an invoice by its ID.

        Args:
            request: The HTTP request object.
            invoice_id: The ID of the invoice to be deleted.

        Returns:
            Response: A JSON response indicating the result of the deletion attempt.
        """
        # Retrieve the invoice object
        this_invoice = get_object_or_404(
            Invoice,
            id=invoice_id,
            is_deleted=False,

        )

        # Create an InvoiceService instance
        invoice_service = DeleteInvoiceService(request.user, this_invoice)

        try:
            # Call the service to delete the invoice
            invoice_service.delete_invoice()

            # Return a successful response
            return Response(
                {"message": "Invoice deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except PermissionDenied as e:
            # Handle unauthorized deletion attempt
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            # Handle other errors during the deletion process
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InvoiceArchiveView(APIView):
    """
    Archives invoice if the user is authorized.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        invoice = get_object_or_404(
            Invoice,
            id=id,
            is_deleted=False,

        )

        # Check if the requesting user is the creator of the bid file
        if invoice.created_by != request.user:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )
        invoice.archive = True
        invoice.save()
        return Response(
            {"message": "invoice archived successfully",
             "data": invoice},
            status=status.HTTP_200_OK,
        )


class InvoicePaymentView(APIView):
    """
    API view to process invoice payments.

    Handles the creation of invoice payment records and the generation of
    associated invoice history. This endpoint expects a POST request with
    form data and files required to process the payment.

    Permissions:
        - Requires the user to be authenticated.

    Methods:
        - post: Process the payment and generate invoice history.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_id):
        """
        Handles the POST request to process an invoice payment.

        Args:
            request (Request): The HTTP request object containing user data,
                form data, and uploaded files.
            invoice_id (int): The ID of the invoice to process the payment for.

        Returns:
            Response: A success response with the ID of the created invoice
            history or an error response in case of failure.
        """
        # Create the InvoicePaymentService to process the payment
        service = InvoicePaymentService(
            request.user,
            invoice_id,
            form_data=request.data,
            files=request.FILES,
        )
        try:
            # Process the payment and generate invoice history
            invoice_history = service.process_payment()

            # Return success message
            return Response(
                {"message": "Invoice payment processed successfully", "invoice_history_id": invoice_history.id},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Return error response in case of failure
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class InvoicePaymentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, transaction_id):
        """
        Handle deletion of an InvoiceTransaction.
        Deletion of associated InvoiceHistory may also occur if needed.
        """
        # Get the InvoiceTransaction object or return 404 if not found
        this_transaction = get_object_or_404(
            InvoiceTransaction,
            id=transaction_id,
            is_deleted=False,

        )
        invoice_id = this_transaction.invoice.id

        # Check if the current user is the one who created the transaction
        if this_transaction.created_by != request.user:
            raise PermissionDenied("You are not authorized to delete this transaction.")

        # Calculate totals for the invoice to potentially delete the InvoiceHistory
        total_invoiced = calculate_total_amount_due(this_transaction.invoice)
        total_paid = calculate_total_paid(this_transaction.invoice)
        balance_due = calculate_remaining_invoice_due(this_transaction.invoice)
        try:
            # Try to delete the associated InvoiceHistory
            this_invoice_history = get_object_or_404(
                InvoiceHistory,
                invoice=this_transaction.invoice,
                total_invoiced=total_invoiced,
                total_paid=total_paid,
                balance_due=balance_due,
                is_deleted=False,

            )
            this_invoice_history.soft_delete()
        except InvoiceHistory.DoesNotExist:
            pass  # If no history is found, just continue without raising an error
        # Delete the InvoiceTransaction record
        this_transaction.soft_delete()
        return Response(
            {"detail": "Transaction deleted successfully."},
            status=status.HTTP_200_OK,
        )


class InvoiceHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        invoice = get_object_or_404(
            Invoice,
            id=invoice_id,
            is_deleted=False,

        )
        invoice_histories = InvoiceHistory.objects.filter(invoice=invoice)
        invoice_history_data = [
            {
                "id": history.id,
                "created_on": history.created_on,
                "total_invoiced": history.total_invoiced,
                "total_paid": history.total_paid,
                "balance_due": history.balance_due,
                "pdf_filename": history.pdf_filename,
            }
            for history in invoice_histories
        ]
        data = {
            "invoice": invoice,
            "invoice_histories": invoice_history_data,
            "WEB_URL": settings.WEB_URL,
            "MEDIA_URL": settings.MEDIA_URL,
        }
        return Response(data, status=status.HTTP_200_OK)


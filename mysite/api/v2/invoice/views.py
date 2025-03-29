import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from datetime import datetime, timedelta

from mysite.api.v2.invoice.serializers import InvoiceSerializer, InvoiceHistorySerializer, InvoiceTransactionSerializer, \
    MassPaymentSerializer
from mysite.core.models import ContactInfo, Company
from mysite.gi.models import Invoice, InvoiceHistory, InvoiceTransaction
from mysite.order.models import Order
from .services.email_service import InvoiceEmailService
from .services.invoice_services import InvoiceService, DeleteInvoiceService
from .services.invoice_list_service import ListInvoiceService
from ..estimator.serializers import EmailSerializer
from ..order.serializers import OrderSerializer
from mysite.order.templatetags.order_tags import (
    calculate_total_amount_due,
    calculate_total_paid,
    calculate_remaining_invoice_due
)

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
    @swagger_auto_schema(
        operation_description="Retrieve a filtered and paginated list of invoices.",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Filter invoices by project name or project number",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "paginate_by",
                openapi.IN_QUERY,
                description="Number of records per page (default: `settings.PAGE_SIZE`)",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Order results by a field (default: `-created_on`)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date for filtering invoices (`MM/DD/YYYY` format)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date for filtering invoices (`MM/DD/YYYY` format)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "type",
                openapi.IN_QUERY,
                description="Filter by invoice status (e.g., `fully-paid`, `partial-paid`, `not-paid`, `old-estimate`)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "overdue",
                openapi.IN_QUERY,
                description="Filter overdue invoices (pass `1` for true, default is false)",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination (default: `1`)",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                "Successful response with paginated list of invoices",
                InvoiceSerializer(many=True),
            ),
            400: "Invalid request parameters",
        },
    )
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
        - PUT: Fully update an invoice with new data.
        - PATCH: Partially update an invoice with new data.

    Permissions:
        - Requires authentication (`IsAuthenticated`).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Fully Update an Invoice",
        description="Updates an invoice by replacing all fields with new data.",
        request=InvoiceSerializer,
        responses={200: InvoiceSerializer},
        parameters=[
            OpenApiParameter(
                name="invoice_id",
                description="The ID of the invoice to update.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    )
    def put(self, request, invoice_id):
        """
        Fully update an invoice.

        Args:
            request (Request): The incoming HTTP request with invoice data.
            invoice_id (int): The ID of the invoice to update.

        Returns:
            Response: Updated invoice data or validation errors.
        """
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        serializer = InvoiceSerializer(invoice, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_invoice = InvoiceService.update_invoice(invoice, serializer.validated_data, request)
            return Response(InvoiceSerializer(updated_invoice).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially Update an Invoice",
        description="Updates an invoice by modifying only the provided fields.",
        request=InvoiceSerializer,
        responses={200: InvoiceSerializer},
        parameters=[
            OpenApiParameter(
                name="invoice_id",
                description="The ID of the invoice to update.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    )
    def patch(self, request, invoice_id):
        """
        Partially update an invoice.

        Args:
            request (Request): The incoming HTTP request with partial invoice data.
            invoice_id (int): The ID of the invoice to update.

        Returns:
            Response: Updated invoice data or validation errors.
        """
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

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

        serializer = InvoiceSerializer(invoice, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)

        # try:
        #     data = DetailedInvoiceService.process_invoice(
        #         invoice=invoice,
        #         user=request.user,
        #     )
        #     return Response(invoice, status=status.HTTP_200_OK)

        # except Exception as e:
        #     logger.error(
        #         f"Error processing invoice {invoice_id}: {str(e)}"
        #     )
        #     return Response(
        #         {"error": "An error occurred while processing the invoice."},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )


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


class InvoiceTransactionCreateView(CreateAPIView):
    """
    API View to create an invoice transaction and log the related invoice history.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceTransactionSerializer

    @extend_schema(
        summary="Create an Invoice Transaction and Log Invoice History",
        description="Takes `invoice_id` from request input, validates the invoice, saves the transaction, and logs the history.",
        request=InvoiceTransactionSerializer,
        responses={201: {
            "transaction": InvoiceTransactionSerializer,
            "invoice_history": InvoiceHistorySerializer
        }},
        parameters=[
            OpenApiParameter(
                name="invoice_id",
                description="The ID of the invoice to create a transaction for.",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
            )
        ],
    )
    def post(self, request):
        """
        Creates an InvoiceTransaction and updates the InvoiceHistory.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: JSON response containing the new transaction and updated history.
        """
        invoice_id = request.data.get("invoice_id")
        if not invoice_id:
            return Response({"error": "invoice_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate that the invoice exists and is not deleted
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        # Serialize and save transaction
        transaction_serializer = InvoiceTransactionSerializer(data=request.data, context={"request": request})
        if transaction_serializer.is_valid():
            transaction_serializer.save()

            # Calculate updated invoice amounts
            total_invoiced = calculate_total_amount_due(invoice)
            total_paid = calculate_total_paid(invoice)
            balance_due = calculate_remaining_invoice_due(invoice)

            # Generate a unique PDF filename for history
            total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1
            new_file_name = f'Invoice-{invoice.order.project_number[:3]}-{invoice.id:03d}-{total_count}'

            # Create invoice history log
            history_data = {
                "invoice_id": invoice.id,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance_due": balance_due,
                "pdf_filename": new_file_name,
            }
            history_serializer = InvoiceHistorySerializer(data=history_data)
            if history_serializer.is_valid():
                history_serializer.save()
                return Response(
                    {
                        "transaction": transaction_serializer.data,
                        "invoice_history": history_serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        return Response(transaction_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceTransactionUpdateView(APIView):
    """
    API View to update an existing InvoiceTransaction.

    - If `amount` or `payment_date` is updated, update the related InvoiceHistory.
    - Otherwise, update only the transaction itself.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Fully Update an Invoice Transaction",
        description="Replaces all fields of an existing invoice transaction with new data. If amount or payment_date is changed, the related InvoiceHistory will be updated.",
        request=InvoiceTransactionSerializer,
        responses={200: InvoiceTransactionSerializer},
        parameters=[
            OpenApiParameter(
                name="transaction_id",
                description="The ID of the transaction to update.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    )
    def put(self, request, transaction_id):
        """
        Fully update an InvoiceTransaction.

        - If `amount` or `payment_date` is updated, update InvoiceHistory.
        """
        transaction = get_object_or_404(InvoiceTransaction, id=transaction_id)

        # Ensure the transaction was created by the current user
        if transaction.created_by != request.user:
            return Response(
                {"error": "You are not authorized to update this transaction."},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_amount = transaction.amount
        old_payment_date = transaction.payment_date

        serializer = InvoiceTransactionSerializer(transaction, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_transaction = serializer.save()

            # Check if payment amount or date changed
            if (
                old_amount != updated_transaction.amount
                or old_payment_date != updated_transaction.payment_date
            ):
                self._update_invoice_history(updated_transaction.invoice)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially Update an Invoice Transaction",
        description="Modifies only the provided fields of an existing invoice transaction. If amount or payment_date is changed, the related InvoiceHistory will be updated.",
        request=InvoiceTransactionSerializer,
        responses={200: InvoiceTransactionSerializer},
        parameters=[
            OpenApiParameter(
                name="transaction_id",
                description="The ID of the transaction to update.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    )
    def patch(self, request, transaction_id):
        """
        Partially update an InvoiceTransaction.

        - If `amount` or `payment_date` is updated, update InvoiceHistory.
        """
        transaction = get_object_or_404(InvoiceTransaction, id=transaction_id)

        # Ensure the transaction was created by the current user
        if transaction.created_by != request.user:
            return Response(
                {"error": "You are not authorized to update this transaction."},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_amount = transaction.amount
        old_payment_date = transaction.payment_date

        serializer = InvoiceTransactionSerializer(transaction, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_transaction = serializer.save()

            # Check if payment amount or date changed
            if (
                old_amount != updated_transaction.amount
                or old_payment_date != updated_transaction.payment_date
            ):
                self._update_invoice_history(updated_transaction.invoice)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _update_invoice_history(self, invoice):
        """
        Recalculates invoice history when a transaction is updated.
        """
        total_invoiced = calculate_total_amount_due(invoice)
        total_paid = calculate_total_paid(invoice)
        balance_due = calculate_remaining_invoice_due(invoice)

        # Fetch or create InvoiceHistory for the invoice
        history, created = InvoiceHistory.objects.get_or_create(invoice=invoice)

        # Update values
        history.total_invoiced = total_invoiced
        history.total_paid = total_paid
        history.balance_due = balance_due
        history.save()


class InvoiceTransactionDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, transaction_id):
        """
        Handle deletion of an InvoiceTransaction.
        Deletion of associated InvoiceHistory may also occur if needed.
        """
        this_transaction = get_object_or_404(
            InvoiceTransaction,
            id=transaction_id,
            is_deleted=False,
        )

        # Check if the current user is the one who created the transaction
        if this_transaction.created_by != request.user:
            raise PermissionDenied("You are not authorized to delete this transaction.")
        invoice = this_transaction.invoice
        # Calculate totals for the invoice to potentially delete the InvoiceHistory
        total_invoiced = calculate_total_amount_due(invoice)
        total_paid = calculate_total_paid(invoice)
        balance_due = calculate_remaining_invoice_due(invoice)
        try:
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
            pass
        this_transaction.soft_delete()
        return Response(
            {"detail": "Transaction deleted successfully."},
            status=status.HTTP_200_OK,
        )


class InvoiceTransactionListView(ListAPIView):
    """
    API View to list all transactions for a specific invoice.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceTransactionSerializer

    @extend_schema(
        summary="List Invoice Transactions",
        description="Fetches a list of all transactions associated with a specific invoice.",
        responses={200: InvoiceTransactionSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="invoice_id",
                description="The ID of the invoice whose transactions should be retrieved.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    )
    def get(self, request, invoice_id):
        """
        Retrieve all transactions for a given invoice.

        Args:
            request (Request): The incoming HTTP request.
            invoice_id (int): The ID of the invoice.

        Returns:
            Response: List of transactions related to the invoice.
        """
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        transactions = InvoiceTransaction.objects.filter(invoice=invoice)
        serializer = InvoiceTransactionSerializer(transactions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class InvoiceHistoryListView(ListAPIView):
    """
    API View to list all invoice history records for a specific invoice.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceHistorySerializer

    @extend_schema(
        summary="List Invoice History Records",
        description="Fetches a list of all history records associated with a specific invoice.",
        responses={200: InvoiceHistorySerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="invoice_id",
                description="The ID of the invoice whose history records should be retrieved.",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    )
    def get(self, request, invoice_id):
        """
        Retrieve all invoice history records for a given invoice.

        Args:
            request (Request): The incoming HTTP request.
            invoice_id (int): The ID of the invoice.

        Returns:
            Response: List of history records related to the invoice.
        """
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        history_records = InvoiceHistory.objects.filter(invoice=invoice)
        serializer = InvoiceHistorySerializer(history_records, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class MassPaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=MassPaymentSerializer,
        responses={
            200: "Payment processed successfully",
            400: "Invalid data provided",
        }
    )
    def post(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        invoices = Invoice.objects.filter(order__proposal__estimate__customer__company__id=company_id)
        if not invoices:
            return Response(
                {"message": "No invoices found for given company_id."},
                 status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MassPaymentSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "message": "Payment processed successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class MassPaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve a list of mass payments",
        operation_description="Fetch paginated mass payments with optional filters like date range and ordering.",
        manual_parameters=[
            openapi.Parameter(
                "fromDate",
                openapi.IN_QUERY,
                description="Start date (MM/DD/YYYY)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "toDate",
                openapi.IN_QUERY,
                description="End date (MM/DD/YYYY)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Order by field (default: '-created_on')",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    )

    def get(self, request, *args, **kwargs):
        """Retrieve a paginated list of mass payments with filters and company-related invoices."""
        # Fetch query parameters
        ordering = request.GET.get("ordering", "-created_on")
        from_date = request.GET.get("fromDate", "04/01/2020")
        to_date = request.GET.get("toDate", "01/01/2100")
        company_id = kwargs.get("company_id")

        try:
            # Convert date strings to datetime objects
            from_date_obj = datetime.strptime(from_date, "%m/%d/%Y")
            to_date_obj = datetime.strptime(to_date, "%m/%d/%Y") + timedelta(
                hours=23, minutes=59, seconds=59
            )
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use MM/DD/YYYY."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch account summaries filtered by company_id
        object_list = Invoice.objects.filter(
            created_on__range=(from_date_obj, to_date_obj),
            order__proposal__estimate__customer__company__id=company_id,
        ).order_by(ordering)

        # Paginate results
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))
        page = paginator.paginate_queryset(object_list, request)

        # Serialize paginated data
        company = Company.objects.get(id=company_id)

        if not company:
            return Response(
                {"error": "No valid company found for the provided criteria."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MassPaymentSerializer(company)

        if not page:
            return paginator.get_paginated_response(serializer.data)

        return paginator.get_paginated_response(serializer.data)


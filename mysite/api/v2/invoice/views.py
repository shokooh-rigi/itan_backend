import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from decimal import Decimal
from rest_framework.exceptions import ValidationError

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
)

from mysite.api.v2.invoice.serializers import (
    InvoiceSerializer,
    InvoiceHistorySerializer,
    InvoiceTransactionSerializer,
    MassPaymentSerializer, InvoiceUpdateSerializer,
)
from mysite.core.models import Company
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
    calculate_remaining_invoice_due,
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
        search = request.GET.get("search", "")
        paginate_by = int(request.GET.get("paginate_by", settings.PAGE_SIZE))
        ordering = request.GET.get("ordering", "-created_on")
        from_date = request.GET.get("fromDate")
        to_date = request.GET.get("toDate")
        invoice_type = request.GET.get(
            "type"
        )  # e.g., 'fully-paid', 'partial-paid', 'not-paid', 'old-estimate'
        overdue = request.GET.get("overdue", "0") == "1"

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
        page_number = request.GET.get("page", 1)
        paginated_invoices = paginator.get_page(number=page_number)

        # Serialize and return response
        serializer = InvoiceSerializer(paginated_invoices, many=True)
        print(serializer.data)
        overdue_days = ListInvoiceService.get_overdue_days()

        return Response(
            {
                "invoices": serializer.data,
                "pagination": {
                    "total_rows": paginator.count,
                    "total_pages": paginator.num_pages,
                    "current_page": paginated_invoices.number,
                    "page_size": paginate_by,
                },
                "overdue_days": overdue_days,
                "overdue_result": overdue,
            },
            status=status.HTTP_200_OK,
        )

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
            invoice_id = serializer.validated_data["email_id"]
            to_email = serializer.validated_data["to_email"]
            cc = serializer.validated_data.get("cc", "")
            subject = serializer.validated_data["subject"]

            success = InvoiceEmailService.send_invoice_email(
                invoice_id, to_email, cc, subject
            )
            if success:
                return Response(
                    {"message": "Invoice sent successfully!"}, status=status.HTTP_200_OK
                )

            return Response(
                {"error": "Failed to send invoice."}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve non-archived and unassociated orders",
        operation_description=(
            "This endpoint retrieves orders that are not archived and not associated with any invoice."
        ),
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination (default: 1)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of records per page (default: 10)",
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
        Retrieves available orders that are not archived or associated with an invoice.
        """
        try:
            orders = (
                Order.objects.filter(archive=False, is_deleted=False)
                .exclude(id__in=Invoice.objects.values_list("order_id", flat=True))
                .order_by("-created_on")
            )

            if order_id:
                orders = orders.filter(id=order_id)

            if not orders.exists():
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
            required=[
                "order_id",
                "invoice_type",
                "date_started",
                "date_completed",
                "terms",
                "description",
            ],
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
        order_id = request.data.get("order_id")
        if not order_id:
            return Response(
                {"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(
            Order,
            id=order_id,
            is_deleted=False,
        )

        serializer = InvoiceSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            invoice = InvoiceService.create_invoice(
                validated_data=serializer.validated_data,
                request_user=request.user,
            )
            return Response(
                {
                    "invoice_id": invoice.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceUpdateView(APIView):
    """
    API View for updating an Invoice.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Fully Update an Invoice",
        operation_description="Updates an invoice by replacing all fields with new data.",
        request_body=InvoiceUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Successful update",
                schema=InvoiceUpdateSerializer()
            )
        },
        manual_parameters=[
            openapi.Parameter(
                name="invoice_id",
                in_=openapi.IN_PATH,
                description="The ID of the invoice to update.",
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ],
    )
    def put(self, request, invoice_id):
        """
        Fully update an invoice.
        """
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        serializer = InvoiceUpdateSerializer(
            invoice, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            updated_invoice = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Partially Update an Invoice",
        operation_description="Updates an invoice by modifying only the provided fields.",
        request_body=InvoiceUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Successful update",
                schema=InvoiceUpdateSerializer()
            )
        },
        manual_parameters=[
            openapi.Parameter(
                name="invoice_id",
                in_=openapi.IN_PATH,
                description="The ID of the invoice to update.",
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ],
    )
    def patch(self, request, invoice_id):
        """
        Partially update an invoice.
        """
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        serializer = InvoiceUpdateSerializer(
            invoice, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

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

    def delete(self, request, id):
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
            id=id,
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
            {"message": "invoice archived successfully", "data": invoice},
            status=status.HTTP_200_OK,
        )


class InvoiceTransactionCreateView(CreateAPIView):
    """
    API View to create an invoice transaction and log the related invoice history.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceTransactionSerializer

    @swagger_auto_schema(
        operation_summary="Create an Invoice Transaction and Log Invoice History",
        operation_description="Takes `invoice_id` from request input, validates the invoice, saves the transaction, and logs the history.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "invoice_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="The ID of the invoice to create a transaction for.",
                    example=123,
                ),
                "payment_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="date",
                    description="The date of the payment.",
                    example="2023-10-01",
                ),
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format="float",
                    description="The amount of the payment.",
                    example=100.50,
                ),
                "payment_no": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The payment number or reference.",
                    example="PAY12345",
                ),
            },
            required=["invoice_id", "payment_date", "amount", "payment_no"],
        ),
        responses={
            201: openapi.Response(
                description="Transaction and Invoice History created successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "transaction": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Details of the created transaction.",
                        ),
                        "invoice_history": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Details of the created invoice history.",
                        ),
                    },
                ),
            ),
            400: "Bad Request - Validation failed",
        },
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
            return Response(
                {"error": "invoice_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that the invoice exists and is not deleted
        invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False)

        # Convert amount to Decimal
        try:
            request.data["amount"] = Decimal(request.data.get("amount"))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid amount. Please provide a valid decimal number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serialize and save transaction
        transaction_serializer = InvoiceTransactionSerializer(
            data=request.data, context={"request": request}
        )
        if not transaction_serializer.is_valid():
            logger.debug(f"Serializer errors: {transaction_serializer.errors}")
            return Response(transaction_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Calculate updated invoice amounts
        total_invoiced = calculate_total_amount_due(invoice)
        total_paid = calculate_total_paid(invoice)
        balance_due = calculate_remaining_invoice_due(invoice)

        if balance_due < 0:
            return Response(
                {"error": "Payment exceeds the invoice amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction_serializer.save()

        # Generate a unique PDF filename for history
        total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1
        new_file_name = f"Invoice-{invoice.order.project_number[:3]}-{invoice.id:03d}-{total_count}"

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

        # Handle invalid history_serializer
        logger.debug(f"History serializer errors: {history_serializer.errors}")
        return Response(history_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        serializer = InvoiceTransactionSerializer(
            transaction, data=request.data, context={"request": request}
        )
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

        serializer = InvoiceTransactionSerializer(
            transaction, data=request.data, partial=True, context={"request": request}
        )
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


class MassPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve a list of invoices",
        operation_description="Fetch invoices",
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a paginated list of mass payments with filters and company-related invoices."""
        company_id = kwargs.get("company_id")

        company = Company.objects.get(id=company_id)

        serializer = MassPaymentSerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        serializer = MassPaymentSerializer(company)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

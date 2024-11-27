import datetime
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import BadHeaderError
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.api.v2.invoice.serializers import InvoiceSerializer, AccountSummarySerializer
from mysite.core.models import ModulesToEmailTemplateRelation, LicenseInfo, ContactInfo
from mysite.gi.models import Invoice, InvoiceHistory, InvoiceTransaction, AccountSummary
from mysite.order.models import Order
from mysite.order.templatetags.order_tags import calculate_total_amount_due, calculate_total_paid, \
    calculate_remaining_invoice_due
from .services.account_summary_service import AccountSummaryService
from .services.email_service import InvoiceEmailService
from .services.invoice_detail_service import DetailedInvoiceService
from .services.invoice_payment_service import InvoicePaymentService
from .services.invoice_services import InvoiceService, DeleteInvoiceService
from .services.ivnoice_list_service import ListInvoiceService
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


class InvoiceCreateView(APIView):
    """
    Handles the creation and retrieval of invoices.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve orders for invoice creation.",
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_PATH,
                description="The ID of the order to retrieve.",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="A list of orders.",
                schema=OrderSerializer(many=True)
            ),
            400: "Bad Request"
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve orders for invoice creation.
        """
        order_id = kwargs.get('order_id')
        if order_id:
            orders = Order.objects.filter(id=order_id)
        else:
            orders = Order.objects.filter(
                archive=False
            ).exclude(
                id__in=Invoice.objects.values_list('order_id', flat=True)
            ).order_by('-created_on')

        # Serialize the orders
        result = OrderSerializer(orders, many=True).data
        return Response({'orders': result}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new invoice for a specific order.",
        request_body=InvoiceSerializer,
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_PATH,
                description="The ID of the order for which the invoice is created.",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            201: openapi.Response(
                description="Invoice created successfully.",
                examples={
                    "application/json": {
                        "invoice_id": 123,
                        "status": "success"
                    }
                }
            ),
            400: "Bad Request"
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new invoice for a specific order.
        """
        order_id = kwargs.get('order_id')
        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the order or return 404
        order = get_object_or_404(Order, id=order_id)
        if not order:
            return Response(
                {'error': 'order not found '},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InvoiceSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            # Call the service layer to create the invoice
            invoice, pdf_params = InvoiceService.create_invoice(
                validated_data=serializer.validated_data,
                request_user=request.user,
            )
            return Response(
                {'invoice_id': invoice.id,
                 "parameters": pdf_params,
                 'status': 'success'},
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
        invoice = get_object_or_404(Invoice, id=invoice_id)
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
        invoice = get_object_or_404(Invoice, id=invoice_id)
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

    @swagger_auto_schema(
        operation_description="Retrieves the details of the specified invoice and processes it if necessary.")
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
        invoice = get_object_or_404(Invoice, id=invoice_id)

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
        this_invoice = get_object_or_404(Invoice, id=invoice_id)

        # Create an InvoiceService instance
        invoice_service = DeleteInvoiceService(request.user, this_invoice)

        try:
            # Call the service to delete the invoice
            invoice_service.delete_invoice()

            # Return a successful response
            return Response(
                {"message": "Invoice deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
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
    Archives invoice if the user is authorized and confirms the action.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        invoice = get_object_or_404(Invoice, id=id)

        # Check if the requesting user is the creator of the bid file
        if invoice.created_by != request.user:
            return Response(
                {"error": "You are not authorized to archive this record."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Confirm archiving action
        if request.data.get("confirm"):
            invoice.archive = True
            invoice.save()
            return Response(
                {"message": "invoice archived successfully",
                 "data": invoice},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Confirmation not received for archiving."},
            status=status.HTTP_400_BAD_REQUEST,
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
        Handle deletion of an InvoiceTransaction. User must confirm by sending "confirm" in the request data.
        Deletion of associated InvoiceHistory may also occur if needed.
        """
        # Get the InvoiceTransaction object or return 404 if not found
        this_transaction = get_object_or_404(InvoiceTransaction, id=transaction_id)
        invoice_id = this_transaction.invoice.id

        # Check if the current user is the one who created the transaction
        if this_transaction.created_by != request.user:
            raise PermissionDenied("You are not authorized to delete this transaction.")

        # If the user confirms the deletion, proceed with the operation
        if request.data.get("confirm"):
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
                )
                this_invoice_history.delete()
            except InvoiceHistory.DoesNotExist:
                pass  # If no history is found, just continue without raising an error
            # Delete the InvoiceTransaction record
            this_transaction.delete()
            return Response(
                {"detail": "Transaction deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        # If confirmation is not provided in the request
        return Response(
            {"error": "Confirmation is required to delete the transaction."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
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


class AccountSummaryAPIView(APIView):
    """
    API endpoint for managing Account Summaries.

    **Methods**:
    - `GET`: Fetch paginated account summaries with optional filters and ordering.
    - `POST`: Send an account summary email with customized content.

    **Parameters (GET)**:
    - `paginate_by` (int): Number of items per page. Default: 20.
    - `ordering` (str): Ordering field, e.g., '-created_on' or 'created_on'.
    - `fromDate` (str): Start date filter in 'MM/DD/YYYY' format. Default: '04/01/2020'.
    - `toDate` (str): End date filter in 'MM/DD/YYYY' format. Default: '01/01/2100'.

    **Parameters (POST)**:
    - `to_email` (str): Recipient email(s), separated by commas.
    - `cc` (str, optional): CC email(s), separated by commas.
    - `subject` (str): Email subject.
    - `email_id` (int): ID of the account summary email to attach.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve a paginated list of account summaries.

        Filters:
        - Filter by date range (`fromDate`, `toDate`).
        - Order by the specified field (`ordering`).
        """
        # Extract query parameters
        ordering = request.GET.get('ordering', '-created_on')
        from_date = request.GET.get("fromDate", '04/01/2020')
        to_date = request.GET.get("toDate", '01/01/2100')

        # Parse date range
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y') + datetime.timedelta(
            hours=23, minutes=59, seconds=59
        )

        # Query and paginate data
        object_list = AccountSummary.objects.filter(
            created_on__range=(from_date_obj, to_date_obj)
        ).order_by(ordering)
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('paginate_by', 20))
        page = paginator.paginate_queryset(object_list, request)

        # Serialize results
        serialized_data = [
            {
                "id": obj.id,
                "created_on": obj.created_on,
                "amount_due": obj.amount_due,
                # Add other fields as needed
            }
            for obj in page
        ]
        return paginator.get_paginated_response(serialized_data)

    def post(self, request):
        """
        Send an email containing account summary details.

        **Input**:
        - `to_email`: Recipient email(s), separated by commas.
        - `cc`: Optional CC email(s), separated by commas.
        - `subject`: Subject of the email.
        - `email_id`: ID of the account summary to attach as a PDF.

        **Response**:
        - Success message or validation/error details.
        """
        form_serializer = EmailSerializer(data=request.data)
        if form_serializer.is_valid():
            # Extract validated data
            to_email = form_serializer.validated_data['to_email'].replace(" ", "").split(',')
            cc = form_serializer.validated_data['cc'].replace(" ", "").split(',') if form_serializer.validated_data[
                'cc'] else []
            subject = form_serializer.validated_data['subject']
            email_id = form_serializer.validated_data['email_id']

            # Fetch user and template data
            user = request.user
            user_data = {
                "name": f"{user.first_name} {user.last_name}" if user.last_name else "TAB Technologies, INC. Operator",
                "title": user.profile.title if user.profile.title else "Estimator",
                "cell": user.profile.cell if user.profile.cell else "",
                "tel": user.profile.tel if user.profile.tel else LicenseInfo.objects.get(
                    key='OwnerTel').value + " Office",
            }

            invoice_template = ModulesToEmailTemplateRelation.objects.get(
                module=9).template.content if ModulesToEmailTemplateRelation.objects.filter(
                module=9).exists() else "No template defined."
            footer_template = ModulesToEmailTemplateRelation.objects.get(
                module=5).template.content if ModulesToEmailTemplateRelation.objects.filter(
                module=5).exists() else "No footer template defined."

            # Prepare and send email
            try:
                footer_content = footer_template.replace("[user_name]", user_data['name']) \
                    .replace("[user_title]", user_data['title']) \
                    .replace("[user_cel]", user_data['cell']) \
                    .replace("[user_tel]", user_data['tel'])
                message = f"{invoice_template}<br />{footer_content}"

                msg = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, to_email, cc=cc)
                msg.content_subtype = "html"
                msg.attach_file(f'media/pdfs/accountsummary/AccountSummary-{email_id}.pdf')
                msg.send()
                return Response({"message": "Email sent successfully"}, status=status.HTTP_200_OK)
            except BadHeaderError:
                return Response({"error": "Invalid email header found."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(form_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountSummaryCreateView(APIView):
    """
    Handles the creation of account summaries for customers.

    Features:
    - Validates input using `AccountSummarySerializer`.
    - Calculates remaining invoices and the total amount using the service layer.
    - Generates and attaches a PDF report for the created account summary.
    """
    def post(self, request, customer_id=None):
        """
        Create an Account Summary.

        This endpoint creates an account summary for a customer.
        If no invoices are available, it returns an error.

        - Input:
          - Customer ID or other data via serializer
        - Output:
          - A created account summary object with a downloadable PDF file
        """
        serializer = AccountSummarySerializer(data=request.data)

        if serializer.is_valid():
            # Handle customers dynamically if not provided
            customer = serializer.validated_data.get('customer')
            if not customer:
                if customer_id:
                    customer = ContactInfo.objects.filter(id=customer_id).first()
                else:
                    customer = ContactInfo.objects.filter(
                        company_type__name__iexact='mechanical contractor'
                    ).first()
                if not customer:
                    return Response(
                        {'error': 'No valid customer found for the provided criteria.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Use the service layer to calculate invoices
            customer_invoices, total = AccountSummaryService.calculate_invoices_total(customer)

            if total == 0:
                return Response({'error': "This Customer has no remaining invoices to pay."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Create the account summary
            account_summary = AccountSummaryService.create_account_summary(
                serializer=serializer,
                user=request.user,
                total=total,
            )

            # Generate the PDF
            user_info = {
                'user_name': f"{request.user.first_name or ''} {request.user.last_name or 'TAB Technologies, INC. Operator'}",
                'user_title': request.user.profile.title or 'Estimator',
                'user_signature': request.user.profile.e_sign,
            }

            pdf_name, pdf_path = AccountSummaryService.generate_pdf_for_summary(
                account_summary=account_summary,
                customer_invoices=customer_invoices,
                user_info=user_info,
            )
            result = {
                'pdf_name': pdf_name,
                'pdf_path': pdf_path,
            }
            return Response(
                result,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountSummaryDeleteView(APIView):
    """
    API view for deleting an account summary.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete an account summary",
        description=(
            "Deletes an account summary if the requesting user is the creator. "
            "Requires confirmation via a 'confirm' parameter in the request body."
        ),
        parameters=[
            OpenApiParameter(
                name="account_summary_id",
                description="ID of the account summary to delete",
                required=True,
                type=int,
            ),
        ],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation to delete the account summary.",
                    }
                },
                "required": ["confirm"],
            }
        },
        responses={
            204: "Account summary deleted successfully.",
            400: "Bad request. Confirmation required.",
            403: "Forbidden. User not authorized to delete the account summary.",
            404: "Not found. Account summary does not exist.",
        },
    )
    def delete(self, request, account_summary_id):
        """
        Delete an account summary if the user is the creator and provides confirmation.

        Args:
            request (Request): The HTTP request object containing the confirmation data.
            account_summary_id (int): The ID of the account summary to be deleted.

        Returns:
            Response: A JSON response indicating success or failure of the operation.
        """
        # Retrieve the account summary
        account_summary = get_object_or_404(AccountSummary, id=account_summary_id)

        # Check if the user is the creator of the account summary
        if account_summary.created_by != request.user:
            return Response(
                {"error": "You are not authorized to delete this account summary."},
                status=status.HTTP_403_FORBIDDEN,
            )

        confirm = request.data.get('confirm', False)
        if not confirm:
            return Response(
                {"error": "Confirmation required to delete the account summary."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parameters = {
                'file_name': 'AccountSummary-' + account_summary.statement_no,
            }
            AccountSummary.delete_account_summary_pdf(parameters)
            account_summary.delete()
            return Response(
                {"message": "Account summary deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


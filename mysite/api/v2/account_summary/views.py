import datetime
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import BadHeaderError
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mysite.order.templatetags.order_tags import calculate_remaining_invoice_due
from .serializers import AccountSummarySerializer, \
    AccountSummaryCreateSerializer
from mysite.core.models import ModulesToEmailTemplateRelation, LicenseInfo, Person
from mysite.gi.models import AccountSummary, Invoice
from .services.account_summary_service import AccountSummaryService
from ..estimator.serializers import EmailSerializer

logger = logging.getLogger(__name__)

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
        paginator.page_size = int(request.GET.get('page_size', settings.PAGE_SIZE))
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


class AccountSummaryListView(generics.ListAPIView):
    """
    Retrieve a paginated list of account summaries with optional filters:
    - Filter by date range (`fromDate`, `toDate`).
    - Order by a specified field (`ordering`).
    - Manual pagination instead of using a separate pagination class.
    """

    serializer_class = AccountSummarySerializer

    @swagger_auto_schema(
        operation_summary="Retrieve a list of account summaries",
        operation_description="Fetch paginated account summaries with optional filters like date range and ordering.",
        manual_parameters=[
            openapi.Parameter(
                "fromDate", openapi.IN_QUERY, description="Start date (MM/DD/YYYY)", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "toDate", openapi.IN_QUERY, description="End date (MM/DD/YYYY)", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "ordering", openapi.IN_QUERY, description="Order by field (default: '-created_on')", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "page_size", openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Response(
                description="Paginated account summaries with total due and company invoices.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "account_summaries": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                        "total_due": openapi.Schema(type=openapi.TYPE_NUMBER),
                        "company_invoices": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                    }
                ),
            ),
            400: openapi.Response(description="Invalid request, company not found."),
        }
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a paginated list of account summaries with filters and company-related invoices."""

        # Fetch query parameters
        ordering = request.GET.get("ordering", "-created_on")
        from_date = request.GET.get("fromDate", "04/01/2020")
        to_date = request.GET.get("toDate", "01/01/2100")
        company_id = kwargs.get("company_id")

        try:
            # Convert date strings to datetime objects
            from_date_obj = datetime.strptime(from_date, "%m/%d/%Y")
            to_date_obj = datetime.strptime(to_date, "%m/%d/%Y") + timedelta(hours=23, minutes=59, seconds=59)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use MM/DD/YYYY."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch account summaries filtered by company_id
        object_list = AccountSummary.objects.filter(
            created_on__range=(from_date_obj, to_date_obj),
            customer__company__id=company_id
        ).order_by(ordering)

        # Paginate results
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get("page_size", settings.PAGE_SIZE))
        page = paginator.paginate_queryset(object_list, request)

        # Serialize paginated data
        serializer = AccountSummarySerializer(page, many=True)

        if not page:
            return paginator.get_paginated_response({"account_summaries": [], "total_due": 0, "company_invoices": []})

        company = Person.objects.filter(company__id=company_id).first()

        if not company:
            return Response(
                {"error": "No valid company found for the provided criteria."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch invoices related to the company
        company_invoices = Invoice.objects.filter(
            order__proposal__estimate__customer__company__id=company_id,
            order__proposal__estimate__due_date__gt="2020-01-04",
        ).order_by("created_on")

        # Calculate remaining invoice amounts and filter non-zero invoices
        remaining_due_list = [
            (invoice, calculate_remaining_invoice_due(invoice)) for invoice in company_invoices
        ]
        total_due = sum(due for _, due in remaining_due_list)
        company_invoices = [invoice for invoice, due in remaining_due_list if due > 0]

        # Construct response
        result = {
            "account_summaries": serializer.data,
            "total_due": total_due,
            "company_invoices": company_invoices,
        }
        return paginator.get_paginated_response(result)


class AccountSummaryCreateView(APIView):
    """
    Handles the creation of account summaries for customers.

    Features:
    - Validates input using `AccountSummarySerializer`.
    - Calculates remaining invoices and the total amount using the service layer.
    - Generates and attaches a PDF report for the created account summary.
    """
    permission_classes = [IsAuthenticated]

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
        serializer = AccountSummaryCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Handle customers dynamically if not provided
            customer = serializer.validated_data.get('customer')
            if not customer:
                if customer_id:
                    # todo: dear reza check if it is ok?? and is need update api for account summery??
                    customer = Person.objects.filter(id=customer_id).first()
                else:
                    customer = Person.objects.filter(
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
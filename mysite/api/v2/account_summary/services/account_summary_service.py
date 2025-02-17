from platform import system

from mysite import settings
from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.gi.models import Invoice, AccountSummary
from mysite.order.templatetags.order_tags import calculate_remaining_invoice_due


class AccountSummaryService:
    """
    Handles business logic for Account Summaries.

    This layer includes logic for:
    - Calculating invoices and total amounts.
    - Creating account summaries.
    - Generating PDF files.
    """

    @staticmethod
    def calculate_invoices_total(customer):
        """
        Calculate the total remaining invoices for a customer.
        Exclude fully paid invoices.
        """
        customer_invoices = Invoice.objects.filter(
            order__proposal__estimate__customer__company=customer,
            order__proposal__estimate__due_date__gt="2020-01-04"
        ).order_by('created_on')

        total = sum(float(calculate_remaining_invoice_due(inv)) for inv in customer_invoices)
        customer_invoices = [inv for inv in customer_invoices if calculate_remaining_invoice_due(inv) > 0]

        return customer_invoices, total

    @staticmethod
    def create_account_summary(serializer, user, total):
        """
        Save the account summary with the calculated total.
        """
        return serializer.save(created_by=user, total=total)

    @staticmethod
    def generate_pdf_for_summary(account_summary, customer_invoices, user_info):
        """
        Generate a PDF for the account summary with user and customer data.

        Parameters:
        - account_summary (AccountSummary): The account summary instance.
        - customer_invoices (QuerySet): List of customer invoices.
        - user_info (dict): User-related information including name, title, and signature.

        Returns:
        - str: The file path of the generated PDF.
        """

        # Dynamically fetch all LicenseInfo keys required
        license_keys = [
            'OwnerName', 'OwnerTitle', 'OwnerAddressLine1', 'OwnerAddressLine2',
            'OwnerTel', 'OwnerFax', 'OwnerWeb', 'OwnerMail', 'PDFHeaderText', 'CompanyName'
        ]
        license_info = {
            key.lower(): LicenseInfo.objects.get(key=key).value for key in license_keys
        }

        # Dynamically fetch all LicenseFiles keys required
        license_file_keys = ['OwnerSignature', 'OwnerLogo', 'PDFHeaderLogo']
        license_files = {
            key.lower(): LicenseFiles.objects.get(key=key).value for key in license_file_keys
        }

        # Combine all parameters
        parameters = {
            'account_summary': account_summary,
            'customer_invoices': customer_invoices,
            **user_info,
            **license_info,
            **license_files,
            'file_name': f"AccountSummary-{account_summary.statement_no}",
            'WEB_URL': settings.WEB_URL,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL,
            'os': system(),
        }
        pdf_name, pdf_path = AccountSummary.create_account_summary_pdf(parameters)

        return pdf_name, pdf_path


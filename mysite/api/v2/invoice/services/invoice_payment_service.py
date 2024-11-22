import datetime
from platform import system

from django.conf import settings

from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.gi.models import Invoice, InvoiceHistory
from mysite.order.models import ChangeOrder
from mysite.order.templatetags.order_tags import (
    calculate_total_amount_due,
    calculate_total_paid,
    calculate_remaining_invoice_due
)


class InvoicePaymentService:
    """
    Service class to handle invoice payment processing.

    Attributes:
        user: User object representing the current user.
        invoice: Invoice object retrieved using the provided invoice_id.
        form_data: Dictionary containing form data (optional).
        files: Any files provided during the payment process (optional).
    """

    def __init__(self, user, invoice_id, form_data=None, files=None):
        """
        Initialize the InvoicePaymentService.

        Args:
            user: Current user initiating the process.
            invoice_id: ID of the invoice to process.
            form_data: Form data dictionary (optional).
            files: Uploaded files dictionary (optional).
        """
        self.user = user
        self.invoice = Invoice.objects.get(id=invoice_id)
        self.form_data = form_data
        self.files = files

    def _fetch_license_data(self):
        """
        Fetch all required license data for generating the invoice.

        Returns:
            A dictionary containing license information.
        """
        license_info_keys = [
            "OwnerName", "OwnerTitle", "OwnerAddressLine1", "OwnerAddressLine2",
            "OwnerTel", "OwnerFax", "OwnerWeb", "OwnerMail", "PDFHeaderText", "CompanyName"
        ]
        license_file_keys = ["OwnerSignature", "OwnerLogo", "PDFHeaderLogo"]

        license_info = {
            key: LicenseInfo.objects.get(key=key).value for key in license_info_keys
        }
        license_files = {
            key: LicenseFiles.objects.get(key=key).value for key in license_file_keys
        }

        return {**license_info, **license_files}

    def process_payment(self):
        """
        Process the payment for the invoice and generate the PDF.

        Returns:
            InvoiceHistory object for the processed invoice.
        """
        now_time = datetime.datetime.now().strftime("%m/%d/%Y")

        # Exit if the form is canceled
        if self.form_data.get("cancel"):
            return None

        # Gather user and invoice-specific data
        user_info = {
            "user_name": f"{self.user.first_name or ''} {self.user.last_name or 'TAB Technologies, INC. Operator'}",
            "user_title": self.user.profile.title or "Estimator",
            "user_signature": self.user.profile.e_sign,
        }

        license_data = self._fetch_license_data()
        change_orders = ChangeOrder.objects.filter(order=self.invoice.order, confirmed=True)
        total_amount_due = calculate_total_amount_due(self.invoice)
        total_count = InvoiceHistory.objects.filter(invoice=self.invoice).count() + 1
        new_file_name = f'Invoice-{str(self.invoice.order.project_number[3:]).zfill(3)}-{str(self.invoice.id).zfill(3)}-{str(total_count)}'

        parameters = {
            "now_time": now_time,
            "file_name": new_file_name,
            "total_count": total_count,
            "revision_date": InvoiceHistory.objects.filter(invoice=self.invoice).order_by("-id").first(),
            "invoice": self.invoice,
            "change_orders": change_orders,
            "total_amount_due": total_amount_due,
            "estimate": self.invoice.order.proposal.estimate,
            **license_data,
            **user_info,
            "WEB_URL": settings.WEB_URL,
            "STATIC_URL": settings.STATIC_URL,
            "MEDIA_URL": settings.MEDIA_URL,
            "os": system(),
        }

        # Generate PDF and save invoice history
        Invoice.create_invoice_pdf(parameters)
        total_invoiced = calculate_total_amount_due(self.invoice)
        total_paid = calculate_total_paid(self.invoice)
        balance_due = calculate_remaining_invoice_due(self.invoice)

        new_invoice_history = InvoiceHistory(
            invoice=self.invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=new_file_name,
        )
        new_invoice_history.save()
        return new_invoice_history


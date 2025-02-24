import logging
from platform import system

from django.conf import settings
from django.db import transaction

from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.gi.models import InvoiceHistory, Invoice
from mysite.order.models import ChangeOrder
from mysite.order.templatetags.order_tags import calculate_total_amount_due, calculate_total_paid, \
    calculate_remaining_invoice_due

logger = logging.getLogger(__name__)


class DetailedInvoiceService:
    """
    Service for handling invoice-related operations.

    Methods:
        - process_invoice: Processes an invoice, creates history if necessary, and generates parameters.
    """

    @staticmethod
    def process_invoice(invoice, user):
        """
        Processes an invoice and creates invoice history if none exists.

        Args:
            invoice (Invoice): The invoice to process.
            user (User): The current user initiating the request.

        Returns:
            dict: Invoice details and parameters for rendering or generating PDF.
        """
        latest_invoice_history = DetailedInvoiceService.get_latest_invoice_history(invoice)

        # Check if there's no invoice history
        if not DetailedInvoiceService.invoice_history_exists(invoice):
            license_info, license_files = DetailedInvoiceService.get_license_data()
            parameters = DetailedInvoiceService.prepare_invoice_parameters(
                invoice=invoice,
                user=user,
                license_info=license_info,
                license_files=license_files,
                latest_invoice_history=latest_invoice_history,
            )

            # Generate the invoice PDF
            # invoice_pdf = Invoice.create_invoice_pdf(parameters)
            # parameters["invoice_pdf"] = invoice_pdf[1]

            # Calculate totals
            total_invoiced = calculate_total_amount_due(invoice)
            total_paid = calculate_total_paid(invoice)
            balance_due = calculate_remaining_invoice_due(invoice)

            # Save InvoiceHistory with transaction handling
            with transaction.atomic():
                DetailedInvoiceService.create_invoice_history(invoice, total_invoiced, total_paid, balance_due, parameters["file_name"])

        return {
            "latest_invoice_history": latest_invoice_history,
            "invoice": invoice,
            "estimate": invoice.order.proposal.estimate,
            "WEB_URL": settings.WEB_URL,
            "STATIC_URL": settings.STATIC_URL,
            "MEDIA_URL": settings.MEDIA_URL,
        }

    @staticmethod
    def get_latest_invoice_history(invoice):
        """
        Retrieves the latest invoice history for the given invoice.

        Args:
            invoice (Invoice): The invoice to retrieve history for.

        Returns:
            InvoiceHistory: The latest invoice history.
        """
        return InvoiceHistory.objects.filter(invoice=invoice).order_by("id").last()

    @staticmethod
    def invoice_history_exists(invoice):
        """
        Checks if there is any invoice history for the given invoice.

        Args:
            invoice (Invoice): The invoice to check for history.

        Returns:
            bool: True if invoice history exists, False otherwise.
        """
        return InvoiceHistory.objects.filter(invoice=invoice).exists()

    @staticmethod
    def get_license_data():
        """
        Retrieves all license data (LicenseInfo and LicenseFiles).

        Returns:
            tuple: A tuple containing dictionaries of license info and license files.
        """
        license_info = {item.key: item.value for item in LicenseInfo.objects.all()}
        license_files = {item.key: item.value for item in LicenseFiles.objects.all()}
        return license_info, license_files

    @staticmethod
    def prepare_invoice_parameters(invoice, user, license_info, license_files, latest_invoice_history):
        """
        Prepares the parameters needed for invoice processing, including user and license details.

        Args:
            invoice (Invoice): The invoice being processed.
            user (User): The current user initiating the request.
            license_info (dict): The license information.
            license_files (dict): The license file information.
            latest_invoice_history (InvoiceHistory): The latest invoice history.

        Returns:
            dict: The parameters for rendering or generating the PDF.
        """
        user_name = f"{user.first_name} {user.last_name}" if user.last_name else "TAB Technologies, INC. Operator"
        user_title = user.profile.title or "Estimator"
        user_signature = user.profile.e_sign

        change_orders = ChangeOrder.objects.filter(order=invoice.order, confirmed=True)
        total_amount_due = calculate_total_amount_due(invoice)
        total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1

        parameters = {
            "file_name": f"Invoice-{str(invoice.order.project_number[3:]).zfill(3)}-{str(invoice.id).zfill(3)}-{total_count}",
            "invoice": invoice,
            "total_count": total_count,
            "revision_date": latest_invoice_history,
            "change_orders": change_orders,
            "total_amount_due": total_amount_due,
            "estimate": invoice.order.proposal.estimate,
            **license_info,
            **license_files,
            "company_name": license_info.get("CompanyName"),
            "user_name": user_name,
            "user_title": user_title,
            "user_signature": user_signature,
            "WEB_URL": settings.WEB_URL,
            "STATIC_URL": settings.STATIC_URL,
            "MEDIA_URL": settings.MEDIA_URL,
            "os": system(),
            "invoice_view_page": True,
        }

        return parameters

    @staticmethod
    def create_invoice_history(invoice, total_invoiced, total_paid, balance_due, file_name):
        """
        Creates an invoice history record in the database.

        Args:
            invoice (Invoice): The invoice to create history for.
            total_invoiced (float): The total invoiced amount.
            total_paid (float): The total amount paid.
            balance_due (float): The remaining balance due.
            file_name (str): The name of the generated PDF file.
        """
        InvoiceHistory.objects.create(
            invoice=invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=file_name,
        )

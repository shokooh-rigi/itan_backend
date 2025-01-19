import logging
from datetime import datetime
from platform import system

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction

from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.gi.models import Invoice, InvoiceHistory
from mysite.order.models import ChangeOrder, Order
from mysite.order.templatetags.order_tags import (
    calculate_total_amount_due,
    calculate_total_paid,
    calculate_remaining_invoice_due,
)
from mysite.projectprocess.models import ProjectProcess

logger = logging.getLogger(__name__)


class InvoiceService:
    """
    Service layer for handling Invoice business logic.

    - Encapsulates logic for creating, updating, and processing invoices.
    - Ensures separation of concerns by keeping views and serializers lightweight.
    """

    @staticmethod
    def create_invoice(validated_data, request_user):
        """
        Create and process a new invoice.

        - Sets invoice type based on specific conditions.
        - Handles related logic such as change orders, invoice history, and project processes.

        Args:
            validated_data (dict): The validated invoice data.
            request_user (User): The user creating the invoice.

        Returns:
            Invoice: The newly created invoice instance.
        """
        with transaction.atomic():
            # Create the invoice instance
            invoice = Invoice.objects.create(**validated_data)
            invoice.created_by = request_user

            # Set the invoice type based on conditions
            invoice_type = InvoiceService.determine_invoice_type(validated_data)
            invoice.invoice_type = invoice_type
            invoice.save()

            # Handle other related logic (e.g., change orders, invoice history, and project processes)
            InvoiceService.create_invoice_history(invoice=invoice, total_count=1)
            InvoiceService.update_project_process(invoice)
            pdf_params = InvoiceService.create_invoice_pdf(invoice, request_user)

        return invoice, pdf_params

    @staticmethod
    def update_invoice(instance, validated_data, request_user):
        """
        Update an existing invoice and reprocess related logic.

        Args:
            instance (Invoice): The invoice instance to update.
            validated_data (dict): The updated invoice data.
            request_user (User): The user updating the invoice.

        Returns:
            Invoice: The updated invoice instance.
        """
        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()
            # Set the invoice type based on conditions
            invoice_type = InvoiceService.determine_invoice_type(validated_data)
            instance.invoice_type = invoice_type
            instance.save()
            total_count = InvoiceHistory.objects.filter(invoice=instance).count() + 1
            InvoiceService.create_invoice_history(
                invoice=instance, total_count=total_count
            )
            pdf_params = InvoiceService.create_invoice_pdf(instance, request_user)
            orders = Order.objects.filter(archive=False).exclude(
                id__in=Invoice.objects.all().values_list("order_id")
            )
        response = {
            "invoice": instance,
            "orders": orders,
        }
        return response

    @staticmethod
    def create_invoice_history(invoice, total_count: int = 1):
        """
        Create an InvoiceHistory record for the given invoice.

        Args:
            invoice (Invoice): The invoice instance.
            total_count (int): Then number of InvoiceHistory for related invoice
        """
        total_invoiced = calculate_total_amount_due(invoice)
        total_paid = calculate_total_paid(invoice)
        balance_due = calculate_remaining_invoice_due(invoice)

        InvoiceHistory.objects.create(
            invoice=invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=f"Invoice-{invoice.order.project_number[3:]:03}-{invoice.id:03}-{total_count}",
        )

    @staticmethod
    def create_invoice_pdf(invoice, request_user):
        """
        Generates a PDF for the invoice, including license info and user details.

        Args:
            invoice (Invoice): The invoice instance.
            request_user (User): The user creating the invoice.

        Returns:
            dict: Parameters for generating the invoice PDF.
        """
        # Check user details
        if request_user.last_name == "" or request_user.last_name is None:
            user_name = "TAB Technologies, INC. Operator"
        else:
            user_name = request_user.first_name + " " + request_user.last_name
        if request_user.profile.title == "" or request_user.profile.title is None:
            user_title = "Estimator"
        else:
            user_title = request_user.profile.title
        user_signature = request_user.profile.e_sign

        # Fetch all LicenseInfo at once to reduce DB hits
        license_info_keys = [
            "OwnerName",
            "OwnerTitle",
            "OwnerAddressLine1",
            "OwnerAddressLine2",
            "OwnerTel",
            "OwnerFax",
            "OwnerWeb",
            "OwnerMail",
            "PDFHeaderText",
            "CompanyName",
        ]
        license_info_dict = {
            info.key: info.value
            for info in LicenseInfo.objects.filter(key__in=license_info_keys)
        }

        # Fetch LicenseFiles required for PDF generation
        license_files_keys = ["OwnerSignature", "OwnerLogo", "PDFHeaderLogo"]
        license_files_dict = {
            file.key: file.value
            for file in LicenseFiles.objects.filter(key__in=license_files_keys)
        }
        change_orders = ChangeOrder.objects.filter(order=invoice.order, confirmed=True)

        # Prepare parameters for the invoice PDF
        parameters = {
            "file_name": f"Invoice-{str(invoice.order.project_number[3:]).zfill(3)}-{str(invoice.id).zfill(3)}-1",
            "total_count": "1",
            "invoice": invoice,
            "order": invoice.order,
            "change_orders": change_orders,
            "total_amount_due": calculate_total_amount_due(invoice),
            "estimate": invoice.order.proposal.estimate,
            "license_owner": license_info_dict.get("OwnerName"),
            "owner_title": license_info_dict.get("OwnerTitle"),
            "owner_address_line1": license_info_dict.get("OwnerAddressLine1"),
            "owner_address_line2": license_info_dict.get("OwnerAddressLine2"),
            "owner_tel": license_info_dict.get("OwnerTel"),
            "owner_fax": license_info_dict.get("OwnerFax"),
            "owner_web": license_info_dict.get("OwnerWeb"),
            "owner_mail": license_info_dict.get("OwnerMail"),
            "owner_signature": license_files_dict.get("OwnerSignature"),
            "owner_logo": license_files_dict.get("OwnerLogo"),
            "pdf_header_logo": license_files_dict.get("PDFHeaderLogo"),
            "pdf_header_text": license_info_dict.get("PDFHeaderText"),
            "company_name": license_info_dict.get("CompanyName"),
            "user_name": user_name,
            "user_title": user_title,
            "user_signature": user_signature,
            "WEB_URL": settings.WEB_URL,
            "STATIC_URL": settings.STATIC_URL,
            "MEDIA_URL": settings.MEDIA_URL,
            "os": system(),
            "invoice_view_page": True,
        }

        # Generate the PDF
        invoice_pdf = Invoice.create_invoice_pdf(parameters)
        parameters["invoice_pdf"] = invoice_pdf[1]
        return parameters

    @staticmethod
    def update_project_process(invoice):
        """
        Update or create the ProjectProcess for the associated order.

        Args:
            invoice (Invoice): The invoice instance.
        """
        # Ensure that the project process exists and update it
        project_process, _ = ProjectProcess.objects.get_or_create(order=invoice.order)
        project_process.tech_package = True
        project_process.tech_scheduled = True
        project_process.job_completed = True
        project_process.report_out = True
        project_process.invoiced_date = datetime.now().date()
        project_process.invoiced = True
        project_process.save()

    @staticmethod
    def determine_invoice_type(validated_data):
        """
        Determines the invoice type based on the provided data.

        Args:
            validated_data (dict): The validated invoice data.

        Returns:
            int: The determined invoice type.
        """
        if validated_data.get("predemo_selected") and not validated_data.get(
            "final_selected"
        ):
            return 2
        elif validated_data.get("dalt_selected") and not validated_data.get(
            "final_selected"
        ):
            return 4
        return 1


class DeleteInvoiceService:
    """
    Service class for handling the deletion of an invoice.

    This service ensures the deletion process is atomic, handles related resources like
    the invoice PDF, and updates associated project processes.
    """

    def __init__(self, user, invoice):
        """
        Initialize the service with the user and invoice.

        Args:
            user: The user attempting to delete the invoice.
            invoice: The invoice object to be deleted.
        """
        self.user = user
        self.invoice = invoice

    def delete_invoice(self):
        """
        Deletes the invoice if the user is authorized.

        Ensures all actions (PDF deletion, project updates, and invoice deletion) are
        performed atomically.

        Raises:
            PermissionDenied: If the user is not authorized to delete the invoice.
            Exception: If an error occurs during the deletion process.
        """
        # Ensure that the user is authorized to delete the invoice
        if self.invoice.created_by != self.user:
            raise PermissionDenied(
                "This record was created by another user, you are not authorized to delete it."
            )

        # Begin a transaction to ensure all actions are atomic
        with transaction.atomic():
            # Delete the invoice PDF
            self.delete_invoice_pdf()

            # Update the project process
            self.update_project_process()

            # Delete the invoice record
            self.invoice.delete()

    def delete_invoice_pdf(self):
        """
        Deletes the PDF file associated with the invoice.

        Constructs the file name based on the project number and invoice ID, then
        calls the appropriate method to delete the PDF.
        """
        parameters = {
            "file_name": f"invoice-{str(self.invoice.order.project_number[3:]).zfill(3)}{str(self.invoice.id).zfill(3)}",
        }
        Invoice.delete_invoice_pdf(parameters)

    def update_project_process(self):
        """
        Updates the project process related to the invoice.

        Marks the invoice as not invoiced and removes the invoiced date.

        Raises:
            Exception: If an error occurs while updating the project process.
        """
        try:
            self.invoice.order.projectprocess.invoiced = False
            self.invoice.order.projectprocess.invoiced_date = None
            self.invoice.order.projectprocess.save()
        except Exception as e:
            raise Exception("Error updating the project process") from e

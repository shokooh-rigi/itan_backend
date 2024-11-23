import datetime
import os
import tempfile
from datetime import datetime
from platform import system

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from requests.exceptions import RequestException

from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.gi.models import Invoice, InvoiceHistory
from mysite.order.models import ChangeOrder
from mysite.projectprocess.models import ProjectProcess
from mysite.s3_file_manager import S3


class ListInvoiceService:
    @staticmethod
    def filter_invoices(search=None, from_date=None, to_date=None, ordering=None):
        filters = Q()

        # Add search filter
        if search:
            filters &= (
                    Q(order__project_number__icontains=search) |
                    Q(order__proposal__estimate__project__name__icontains=search)
            )

        # Add date range filter
        if from_date and to_date:
            try:
                from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
                to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y') + datetime.timedelta(
                    days=1) - datetime.timedelta(seconds=1)
                filters &= Q(created_on__range=(from_date_obj, to_date_obj))
            except ValueError:
                raise ValueError("Invalid date format. Please use 'MM/DD/YYYY'.")

        # Handle ordering safely
        ordering = ordering or 'id'
        return Invoice.objects.filter(filters).order_by(ordering)

    @staticmethod
    def send_invoice_email(invoice_id, to_email, cc=None, subject="Invoice"):
        try:
            # Fetch the latest invoice history
            latest_invoice_history = InvoiceHistory.objects.filter(invoice__id=invoice_id).order_by('id').last()
            if not latest_invoice_history:
                raise ValueError(f"No invoice history found for invoice ID {invoice_id}.")

            # Fetch the PDF file from S3
            s3 = S3()  # Consider injecting this dependency for better testability
            pdf_url = s3.get_bucket_object(f'media/pdfs/invoice/{latest_invoice_history.pdf_filename}.pdf')

            response = requests.get(pdf_url)
            response.raise_for_status()  # Raise an HTTPError if the request failed

            # Use a temporary file for the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # Prepare and send the email
            msg = EmailMessage(
                subject=subject,
                body="Invoice content here",  # Replace with actual email content
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
                cc=cc.split(',') if cc else None,
            )
            msg.attach_file(temp_file_path)
            msg.send()

            # Clean up temporary file
            os.remove(temp_file_path)
            return True
        except ValueError as e:
            # Handle specific validation errors
            print(f"Validation error: {e}")
            return False
        except RequestException as e:
            # Handle network errors
            print(f"Error fetching PDF from S3: {e}")
            return False
        except Exception as e:
            # Log unexpected errors
            print(f"Unexpected error occurred: {e}")
            return False


class CreateInvoiceService:
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
        # Create invoice instance
        invoice = Invoice.objects.create(**validated_data)
        invoice.created_by = request_user

        # Determine invoice type
        invoice_type = 1
        if validated_data.get("predemo_selected") and not validated_data.get("final_selected"):
            invoice_type = 2
        elif validated_data.get("dalt_selected") and not validated_data.get("final_selected"):
            invoice_type = 4
        invoice.invoice_type = invoice_type
        invoice.save()

        # Handle related business logic
       # CreateInvoiceService.handle_related_logic(invoice)

        return invoice

    @staticmethod
    def update_invoice(instance, validated_data, request):
        """
        Update an existing invoice and reprocess related logic.

        Args:
            instance (Invoice): The invoice instance to update.
            validated_data (dict): The updated invoice data.
            request (HttpRequest): The HTTP request object.

        Returns:
            Invoice: The updated invoice instance.
        """
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        # Reprocess related logic
      #  InvoiceService.handle_related_logic(instance)

        return instance

    @staticmethod
    def handle_related_logic(invoice):
        """
        Handles all related logic for an invoice, such as history creation and project process updates.

        Args:
            invoice (Invoice): The invoice instance.
        """
        change_orders = ChangeOrder.objects.filter(order=invoice.order, confirmed=True)
        CreateInvoiceService.create_invoice_history(invoice)
        CreateInvoiceService.update_project_process(invoice)

    @staticmethod
    def create_invoice_history(invoice):
        """
        Create an InvoiceHistory record for the given invoice.

        Args:
            invoice (Invoice): The invoice instance.
        """
        total_invoiced = CreateInvoiceService.calculate_total_amount_due(invoice)
        total_paid = CreateInvoiceService.calculate_total_paid(invoice)
        balance_due = CreateInvoiceService.calculate_remaining_invoice_due(invoice)

        InvoiceHistory.objects.create(
            invoice=invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=f'Invoice-{invoice.order.project_number[3:]:03}-{invoice.id:03}-1'
        )

    @staticmethod
    def update_project_process(invoice):
        """
        Update or create the ProjectProcess for the associated order.

        Args:
            invoice (Invoice): The invoice instance.
        """
        project_process, _ = ProjectProcess.objects.get_or_create(order=invoice.order)
        project_process.tech_package = True
        project_process.tech_scheduled = True
        project_process.job_completed = True
        project_process.report_out = True
        project_process.invoiced_date = datetime.datetime.now().date()
        project_process.invoiced = True
        project_process.save()

    @staticmethod
    def calculate_total_amount_due(invoice):
        """
        Calculate the total amount due for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: The total amount due.
        """
        return sum(
            change_order.amount for change_order in ChangeOrder.objects.filter(order=invoice.order, confirmed=True)
        )

    @staticmethod
    def calculate_total_paid(invoice):
        """
        Calculate the total amount paid for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: The total amount paid.
        """
        return sum(payment.amount for payment in invoice.payments.all())

    @staticmethod
    def calculate_remaining_invoice_due(invoice):
        """
        Calculate the remaining balance for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: The remaining balance due.
        """
        return CreateInvoiceService.calculate_total_amount_due(invoice) - CreateInvoiceService.calculate_total_paid(invoice)


class UpdateInvoiceService:
    """
    Service for handling invoice updates and related operations.

    Methods:
        - update_invoice: Updates an invoice and performs related calculations.
        - calculate_total_amount_due: Calculates the total amount due for an invoice.
        - calculate_total_paid: Calculates the total amount paid for an invoice.
        - calculate_remaining_invoice_due: Calculates the remaining balance for an invoice.
    """

    @staticmethod
    @transaction.atomic
    def update_invoice(invoice, validated_data, request):
        """
        Updates an invoice and performs associated operations like history logging and
        project process updates.

        Args:
            invoice (Invoice): The invoice instance to update.
            validated_data (dict): The validated data for updating the invoice.
            request (Request): The request object, used for additional context.

        Returns:
            Invoice: The updated invoice instance.
        """
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(invoice, attr, value)

        # Determine invoice type
        if request.data.get("predemo_selected") and not request.data.get("final_selected"):
            invoice.invoice_type = 2
        elif request.data.get("dalt_selected") and not request.data.get("final_selected"):
            invoice.invoice_type = 4
        else:
            invoice.invoice_type = 1

        # Save the updated invoice
        invoice.save()

        # Perform calculations and log InvoiceHistory
        total_amount_due = UpdateInvoiceService.calculate_total_amount_due(invoice)
        total_paid = UpdateInvoiceService.calculate_total_paid(invoice)
        balance_due = UpdateInvoiceService.calculate_remaining_invoice_due(invoice)

        InvoiceHistory.objects.create(
            invoice=invoice,
            total_invoiced=total_amount_due,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=f'Invoice-{invoice.order.project_number[3:]:03}-{invoice.id:03}-1'
        )

        # Update ProjectProcess
        project_process, _ = ProjectProcess.objects.get_or_create(order=invoice.order)
        project_process.tech_package = True
        project_process.tech_scheduled = True
        project_process.job_completed = True
        project_process.report_out = True
        project_process.invoiced_date = datetime.now().date()
        project_process.invoiced = True
        project_process.save()

        return invoice

    @staticmethod
    def calculate_total_amount_due(invoice):
        """
        Calculates the total amount due for an invoice based on change orders.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: Total amount due.
        """
        return sum(
            change_order.amount for change_order in ChangeOrder.objects.filter(order=invoice.order, confirmed=True))

    @staticmethod
    def calculate_total_paid(invoice):
        """
        Calculates the total amount paid for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: Total amount paid.
        """
        return sum(payment.amount for payment in invoice.payments.all())

    @staticmethod
    def calculate_remaining_invoice_due(invoice):
        """
        Calculates the remaining balance due for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: Remaining balance due.
        """
        return UpdateInvoiceService.calculate_total_amount_due(invoice) - UpdateInvoiceService.calculate_total_paid(
            invoice)


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
        latest_invoice_history = InvoiceHistory.objects.filter(invoice=invoice).order_by("id").last()
        num_results = InvoiceHistory.objects.filter(invoice=invoice).count()

        if num_results == 0:
            # Determine user details
            user_name = (
                "TAB Technologies, INC. Operator"
                if not user.last_name
                else f"{user.first_name} {user.last_name}"
            )
            user_title = user.profile.title or "Estimator"
            user_signature = user.profile.e_sign

            # Prepare invoice-related data
            change_orders = ChangeOrder.objects.filter(order=invoice.order, confirmed=True)
            total_amount_due = DetailedInvoiceService.calculate_total_amount_due(invoice)
            total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1

            # License information
            license_info = {
                "license_owner": LicenseInfo.objects.get(key="OwnerName").value,
                "owner_title": LicenseInfo.objects.get(key="OwnerTitle").value,
                "owner_address_line1": LicenseInfo.objects.get(key="OwnerAddressLine1").value,
                "owner_address_line2": LicenseInfo.objects.get(key="OwnerAddressLine2").value,
                "owner_tel": LicenseInfo.objects.get(key="OwnerTel").value,
                "owner_fax": LicenseInfo.objects.get(key="OwnerFax").value,
                "owner_web": LicenseInfo.objects.get(key="OwnerWeb").value,
                "owner_mail": LicenseInfo.objects.get(key="OwnerMail").value,
            }

            # License files
            license_files = {
                "owner_signature": LicenseFiles.objects.get(key="OwnerSignature").value,
                "owner_logo": LicenseFiles.objects.get(key="OwnerLogo").value,
                "pdf_header_logo": LicenseFiles.objects.get(key="PDFHeaderLogo").value,
                "pdf_header_text": LicenseInfo.objects.get(key="PDFHeaderText").value,
            }

            parameters = {
                "file_name": f"Invoice-{str(invoice.order.project_number[3:]).zfill(3)}-{str(invoice.id).zfill(3)}-{total_count}",
                "invoice": invoice,
                "total_count": total_count,
                "revision_date": InvoiceHistory.objects.filter(invoice=invoice).order_by("-id")[0],
                "change_orders": change_orders,
                "total_amount_due": total_amount_due,
                "estimate": invoice.order.proposal.estimate,
                **license_info,
                **license_files,
                "company_name": LicenseInfo.objects.get(key="CompanyName").value,
                "user_name": user_name,
                "user_title": user_title,
                "user_signature": user_signature,
                "WEB_URL": settings.WEB_URL,
                "STATIC_URL": settings.STATIC_URL,
                "MEDIA_URL": settings.MEDIA_URL,
                "os": system(),
                "invoice_view_page": True,
            }

            # Generate invoice PDF
            invoice_pdf = Invoice.create_invoice_pdf(parameters)
            parameters["invoice_pdf"] = invoice_pdf[1]

            # Calculate totals
            total_invoiced = DetailedInvoiceService.calculate_total_amount_due(invoice)
            total_paid = DetailedInvoiceService.calculate_total_paid(invoice)
            balance_due = DetailedInvoiceService.calculate_remaining_invoice_due(invoice)

            # Save InvoiceHistory
            InvoiceHistory.objects.create(
                invoice=invoice,
                total_invoiced=total_invoiced,
                total_paid=total_paid,
                balance_due=balance_due,
                pdf_filename=parameters["file_name"],
            )

        return {
            "latest_invoice_history": latest_invoice_history,
            "invoice": invoice,
            "estimate": invoice.order.proposal.estimate,
            "WEB_URL": settings.WEB_URL,
            "STATIC_URL": settings.STATIC_URL,
            "MEDIA_URL": settings.MEDIA_URL,
        }

    @staticmethod
    def calculate_total_amount_due(invoice):
        """
        Calculates the total amount due for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: Total amount due.
        """
        return sum(
            change_order.amount
            for change_order in ChangeOrder.objects.filter(order=invoice.order, confirmed=True)
        )

    @staticmethod
    def calculate_total_paid(invoice):
        """
        Calculates the total amount paid for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: Total amount paid.
        """
        return sum(payment.amount for payment in invoice.payments.all())

    @staticmethod
    def calculate_remaining_invoice_due(invoice):
        """
        Calculates the remaining balance due for an invoice.

        Args:
            invoice (Invoice): The invoice instance.

        Returns:
            Decimal: Remaining balance due.
        """
        return DetailedInvoiceService.calculate_total_amount_due(invoice) - DetailedInvoiceService.calculate_total_paid(invoice)


class DeleteInvoiceService:
    def __init__(self, user, invoice):
        self.user = user
        self.invoice = invoice


    def delete_invoice(self):
        # Ensure that the user is authorized to delete the invoice
        if self.invoice.created_by != self.user:
            raise PermissionDenied("This record was created by another user, you are not authorized to delete it.")

        # Begin a transaction to ensure all actions are atomic
        with transaction.atomic():
            # Delete the invoice PDF
            self.delete_invoice_pdf()

            # Update the project process
            self.update_project_process()

            # Delete the invoice record
            self.invoice.delete()

    def delete_invoice_pdf(self):
        parameters = {
            'file_name': f"invoice-{str(self.invoice.order.project_number[3:]).zfill(3)}{str(self.invoice.id).zfill(3)}",
        }
        Invoice.delete_invoice_pdf(parameters)

    def update_project_process(self):
        try:
            self.invoice.order.projectprocess.invoiced = False
            self.invoice.order.projectprocess.invoiced_date = None
            self.invoice.order.projectprocess.save()
        except Exception as e:
            raise Exception("Error updating the project process") from e




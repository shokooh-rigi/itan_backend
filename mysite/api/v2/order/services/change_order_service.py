from platform import system

from mysite import settings
from mysite.api.v2.invoice.services.invoice_services import InvoiceService
from mysite.api.v2.order.serializers import ChangeOrderSerializer
from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.gi.models import InvoiceHistory, Invoice
from mysite.order.models import ChangeOrder
from mysite.order.templatetags.order_tags import calculate_total_amount_due, calculate_total_paid, \
    calculate_remaining_invoice_due


class ChangeOrderServiceLayer:
    """
    Service layer to handle ChangeOrder logic.
    """

    def __init__(self, order, user, data=None):
        self.order = order
        self.user = user
        self.data = data

    def create_change_order(self):
        """
        Create a new ChangeOrder with associated services.
        """
        serializer = ChangeOrderSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        change_order = serializer.save()

        # Generate PDF
        self._generate_pdf(change_order)

        return change_order

    def _generate_pdf(self, change_order):
        """
        Generate the PDF for the created ChangeOrder.
        """
        user_name = self.user.get_full_name() or "TAB Technologies, INC. Operator"
        user_title = getattr(self.user.profile, 'title', 'Estimator')
        user_signature = getattr(self.user.profile, 'e_sign', None)

        pdf_parameters = {
            'file_name': f'ChangeOrder-{str(self.order.project_number[3:]).zfill(3)}-{change_order.co_number}',
            'change_order': change_order,
            'change_order_services': change_order.changeorderservice_set.all(),
            'order': self.order,
            'estimate': self.order.proposal.estimate,
            'license_owner': self._get_license_info('OwnerName'),
            'owner_title': self._get_license_info('OwnerTitle'),
            'owner_address_line1': self._get_license_info('OwnerAddressLine1'),
            'owner_address_line2': self._get_license_info('OwnerAddressLine2'),
            'owner_tel': self._get_license_info('OwnerTel'),
            'owner_fax': self._get_license_info('OwnerFax'),
            'owner_web': self._get_license_info('OwnerWeb'),
            'owner_mail': self._get_license_info('OwnerMail'),
            'owner_signature': self._get_license_files('OwnerSignature'),
            'owner_logo': self._get_license_files('OwnerLogo'),
            'pdf_header_logo': self._get_license_files('PDFHeaderLogo'),
            'pdf_header_text': self._get_license_info('PDFHeaderText'),
            'company_name': self._get_license_info('CompanyName'),
            'user_name': user_name,
            'user_title': user_title,
            'user_signature': user_signature,
            'WEB_URL': settings.WEB_URL,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL,
            'os': system(),
        }
        change_order.create_change_order_pdf(pdf_parameters)

    @staticmethod
    def approve_change_order(change_order_id, action, user):
        # Fetch the ChangeOrder and related order
        this_change_order = ChangeOrder.objects.get(id=change_order_id)
        this_order = this_change_order.order

        # Set the confirmed status based on action
        this_change_order.confirmed = action == "1"
        this_change_order.save()

        # Prepare user-related data (e.g., user name, title, and signature)
        user_name = user.first_name + " " + user.last_name if user.last_name else 'TAB Technologies, INC. Operator'
        user_title = user.profile.title if user.profile.title else 'Estimator'
        user_signature = user.profile.e_sign

        # Get all confirmed change orders
        change_orders = ChangeOrder.objects.filter(order=this_order.invoice.order, confirmed=True)

        # Calculate totals
        total_amount_due = calculate_total_amount_due(this_order.invoice)
        total_count = InvoiceHistory.objects.filter(invoice=this_order.invoice).count() + 1
        new_file_name = f"Invoice-{str(this_order.project_number[3:]).zfill(3)}-{str(this_order.id).zfill(3)}-{str(total_count)}"

        # Prepare the parameters for PDF generation
        pdf_parameters = {
            'file_name': new_file_name,
            'total_count': total_count,
            'revision_date': InvoiceHistory.objects.filter(invoice=this_order.invoice).order_by('-id').first(),
            'invoice': this_order.invoice,
            'change_orders': change_orders,
            'total_amount_due': total_amount_due,
            'estimate': this_order.invoice.order.proposal.estimate,
            'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
            'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
            'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
            'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
            'owner_tel': LicenseInfo.objects.get(key='OwnerTel').value,
            'owner_fax': LicenseInfo.objects.get(key='OwnerFax').value,
            'owner_web': LicenseInfo.objects.get(key='OwnerWeb').value,
            'owner_mail': LicenseInfo.objects.get(key='OwnerMail').value,
            'owner_signature': LicenseFiles.objects.get(key='OwnerSignature').value,
            'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
            'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
            'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
            'company_name': LicenseInfo.objects.get(key='CompanyName').value,
            'user_name': user_name,
            'user_title': user_title,
            'user_signature': user_signature,
            'WEB_URL': settings.WEB_URL,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL,
            'os': system(),
        }

        # Generate the invoice PDF
        Invoice.create_invoice_pdf(pdf_parameters)

        # Create an InvoiceHistory object
        total_invoiced = calculate_total_amount_due(this_order.invoice)
        total_paid = calculate_total_paid(this_order.invoice)
        balance_due = calculate_remaining_invoice_due(this_order.invoice)
        InvoiceHistory.objects.create(
            invoice=this_order.invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=new_file_name
        )

        return new_file_name

    @staticmethod
    def _get_license_info(key):
        return LicenseInfo.objects.get(key=key).value

    @staticmethod
    def _get_license_files(key):
        return LicenseFiles.objects.get(key=key).value


class DeleteChangeOrderService:
    """
    Service layer to handle ChangeOrder logic.
    """

    def __init__(self, order, user):
        self.order = order
        self.user = user

    def delete_change_order(self, change_order):
        """
        Deletes the ChangeOrder and generates a new invoice if necessary.
        """
        try:
            # Generate the file name for the associated PDF to be deleted
            file_name = f'ChangeOrder-{str(self.order.project_number[3:]).zfill(3)}-{change_order.co_number}'
            # Delete the associated PDF first (if applicable)
            change_order.delete_change_order_pdf({'file_name': file_name})

            # Delete the change order itself
            change_order.soft_delete()

            # Create a new invoice
            self._create_invoice()

            return True
        except ChangeOrder.DoesNotExist:
            return False

    def _create_invoice(self):
        """
        Create a new invoice after the change order is deleted.
        """
        # Fetch necessary data to create the invoice PDF
        change_orders = ChangeOrder.objects.filter(order=self.order.invoice.order, confirmed=True)
        total_amount_due = calculate_total_amount_due(self.order.invoice)
        total_count = InvoiceHistory.objects.filter(invoice=self.order.invoice).count() + 1
        new_file_name = f'Invoice-{str(self.order.project_number[3:]).zfill(3)}-{str(self.order.id).zfill(3)}-{str(total_count)}'

        # Invoice PDF parameters
        pdf_parameters = {
            'file_name': new_file_name,
            'total_count': total_count,
            'revision_date': InvoiceHistory.objects.filter(invoice=self.order.invoice).order_by('-id')[0],
            'invoice': self.order.invoice,
            'change_orders': change_orders,
            'total_amount_due': total_amount_due,
            'estimate': self.order.invoice.order.proposal.estimate,
            'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
            'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
            'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
            'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
            'owner_tel': LicenseInfo.objects.get(key='OwnerTel').value,
            'owner_fax': LicenseInfo.objects.get(key='OwnerFax').value,
            'owner_web': LicenseInfo.objects.get(key='OwnerWeb').value,
            'owner_mail': LicenseInfo.objects.get(key='OwnerMail').value,
            'owner_signature': LicenseFiles.objects.get(key='OwnerSignature').value,
            'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
            'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
            'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
            'company_name': LicenseInfo.objects.get(key='CompanyName').value,
            'user_name': self.user.get_full_name(),
            'user_title': self.user.profile.title if self.user.profile.title else 'Estimator',
            'user_signature': self.user.profile.e_sign,
            'WEB_URL': settings.WEB_URL,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL,
            'os': system(),
        }

        # Generate invoice PDF
        InvoiceService.create_invoice_pdf(pdf_parameters)

        # Create an invoice history record
        total_invoiced = calculate_total_amount_due(self.order.invoice)
        total_paid = calculate_total_paid(self.order.invoice)
        balance_due = calculate_remaining_invoice_due(self.order.invoice)
        new_object = InvoiceHistory(
            invoice=self.order.invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=new_file_name
        )
        new_object.save()

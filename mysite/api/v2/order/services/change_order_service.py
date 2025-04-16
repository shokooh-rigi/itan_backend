from mysite.api.v2.order.serializers import ChangeOrderSerializer
from mysite.gi.models import InvoiceHistory
from mysite.order.models import ChangeOrder
from mysite.order.templatetags.order_tags import (
    calculate_total_amount_due,
    calculate_total_paid,
    calculate_remaining_invoice_due,
)


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
        return change_order

    @staticmethod
    def approve_change_order(change_order_id):
        # Fetch the ChangeOrder and related order
        this_change_order = ChangeOrder.objects.get(id=change_order_id)
        this_order = this_change_order.order

        # Set the confirmed status based on action
        this_change_order.confirmed = True
        this_change_order.save()

        # Calculate totals
        total_count = (
            InvoiceHistory.objects.filter(invoice=this_order.invoice).count() + 1
        )
        new_file_name = f"Invoice-{str(this_order.project_number[3:]).zfill(3)}-{str(this_order.id).zfill(3)}-{str(total_count)}"
        total_invoiced = calculate_total_amount_due(this_order.invoice)
        total_paid = calculate_total_paid(this_order.invoice)
        balance_due = calculate_remaining_invoice_due(this_order.invoice)
        InvoiceHistory.objects.create(
            invoice=this_order.invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=new_file_name,
        )

        return this_change_order

    @staticmethod
    def unapprove_change_order(change_order_id):
        # Fetch the ChangeOrder and related order
        this_change_order = ChangeOrder.objects.get(id=change_order_id)
        this_order = this_change_order.order

        # Set the confirmed status based on action
        this_change_order.confirmed = False
        this_change_order.save()

        # Calculate totals
        total_count = (
            InvoiceHistory.objects.filter(invoice=this_order.invoice).count() + 1
        )
        new_file_name = f"Invoice-{str(this_order.project_number[3:]).zfill(3)}-{str(this_order.id).zfill(3)}-{str(total_count)}"
        total_invoiced = calculate_total_amount_due(this_order.invoice)
        total_paid = calculate_total_paid(this_order.invoice)
        balance_due = calculate_remaining_invoice_due(this_order.invoice)
        InvoiceHistory.objects.create(
            invoice=this_order.invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=new_file_name,
        )

        return this_change_order


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
            file_name = f"ChangeOrder-{str(self.order.project_number[3:]).zfill(3)}-{change_order.co_number}"
            # Delete the associated PDF first (if applicable)
            change_order.delete_change_order_pdf({"file_name": file_name})

            # Delete the change order itself
            change_order.soft_delete()

            # Create a new invoice
            self._create_invoice_history()

            return True
        except ChangeOrder.DoesNotExist:
            return False

    def _create_invoice_history(self):
        """
        Create a new invoice after the change order is deleted.
        """
        # Fetch necessary data to create the invoice PDF
        total_count = (
            InvoiceHistory.objects.filter(invoice=self.order.invoice).count() + 1
        )
        new_file_name = f"Invoice-{str(self.order.project_number[3:]).zfill(3)}-{str(self.order.id).zfill(3)}-{str(total_count)}"
        total_invoiced = calculate_total_amount_due(self.order.invoice)
        total_paid = calculate_total_paid(self.order.invoice)
        balance_due = calculate_remaining_invoice_due(self.order.invoice)
        new_object = InvoiceHistory(
            invoice=self.order.invoice,
            total_invoiced=total_invoiced,
            total_paid=total_paid,
            balance_due=balance_due,
            pdf_filename=new_file_name,
        )
        new_object.save()

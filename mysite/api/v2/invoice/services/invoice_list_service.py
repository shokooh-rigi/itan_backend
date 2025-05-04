from datetime import datetime, timedelta
import logging

from django.db.models import Q

from mysite.core.models import Setting
from mysite.gi.models import Invoice

logger = logging.getLogger(__name__)


class ListInvoiceService:
    """
    Service class for filtering and retrieving invoices based on various criteria.
    """

    @staticmethod
    def filter_invoices(
        search=None,
        from_date=None,
        to_date=None,
        ordering=None,
        invoice_type=None,
        overdue=False,
    ):
        """
        Filters invoices based on search query, date range, ordering, type, and overdue status.

        Args:
            search (str, optional): Search query to filter by project name or project number.
            from_date (str, optional): Start date for filtering (format: 'MM/DD/YYYY').
            to_date (str, optional): End date for filtering (format: 'MM/DD/YYYY').
            ordering (str, optional): Field to order the results by (default: 'id').
            invoice_type (str, optional): Type of invoice to filter ('fully-paid', 'partial-paid', 'not-paid', 'old-estimate').
            overdue (bool, optional): Whether to filter invoices that are overdue.

        Returns:
            QuerySet: Filtered queryset of invoices.
        """
        filters = Q()

        # Add search filter
        if search:
            filters &= Q(order__project_number__icontains=search) | Q(
                order__proposal__estimate__project__name__icontains=search
            )

        # Add date range filter
        if from_date and to_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%m/%d/%Y")
                to_date_obj = datetime.strptime(to_date, "%m/%d/%Y") + timedelta(days=1) - timedelta(seconds=1)
                filters &= Q(created_on__range=(from_date_obj, to_date_obj))
            except ValueError:
                raise ValueError("Invalid date format. Please use 'MM/DD/YYYY'.")

        # Add type filter
        if invoice_type:
            filters &= ListInvoiceService.filter_by_type(invoice_type)

        # Add overdue filter
        if overdue:
            overdue_days = ListInvoiceService.get_overdue_days()
            overdue_date = datetime.now() - timedelta(days=int(overdue_days))
            filters &= Q(created_on__lte=overdue_date)

        # Handle ordering safely
        result = Invoice.objects.filter(filters, is_deleted=False)
        if ordering:
            result = result.order_by(ordering)

        return result

    @staticmethod
    def filter_by_type(invoice_type):
        """
        Returns additional filters based on the invoice type.

        Args:
            invoice_type (str): The type of invoice to filter.
                                Options: 'fully-paid', 'partial-paid', 'not-paid', 'old-estimate'.

        Returns:
            Q: Django Q object with the applied type filters.
        """
        if invoice_type == "fully-paid":
            # Filter invoices with balance_due = 0 in the latest InvoiceHistory
            return Q(invoicehistory__balance_due=0)

        elif invoice_type == "partial-paid":
            # Filter invoices with balance_due > 0 and at least one transaction
            return Q(invoicehistory__balance_due__gt=0) & Q(invoicetransaction__isnull=False)

        elif invoice_type == "not-paid":
            # Filter invoices with no transactions
            return Q(invoicetransaction__isnull=True)

        elif invoice_type == "old-estimate":
            # Filter invoices with old due dates and balance_due > 0
            old_due_date = datetime.strptime("04/01/2020", "%m/%d/%Y")
            return Q(order__proposal__estimate__due_date__lte=old_due_date) & Q(invoicehistory__balance_due__gt=0)

        return Q()

    @staticmethod
    def get_overdue_days():
        """
        Fetches the 'Overdue Days' setting from the database.

        Returns:
            int: The number of days after which an invoice is considered overdue.
                 Returns 0 if the setting is not found.
        """
        try:
            return int(Setting.objects.get(key="Overdue Days").value)
        except Setting.DoesNotExist:
            return 0
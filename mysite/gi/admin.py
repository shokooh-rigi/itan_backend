from django.contrib import admin
from mysite.gi.models import (
    Invoice,
    InvoiceTransaction,
    AccountSummary,
    InvoiceHistory
)


class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin page for managing Invoices.
    """
    list_display = [
        "id",
        "order",
        "invoice_number",
        "date_started",
        "date_completed",
        "terms",
        "description",
        "percent_of_performance_completed",
        "invoice_type",
        "attention",
        "mark_as_paid",
        "created_on",
        "updated_at",
    ]
    search_fields = ["id", "order__project_number"]
    list_filter = ["invoice_type", "mark_as_paid", "created_on"]
    readonly_fields = ["invoice_number", "created_on", "updated_at"]
    fieldsets = [
        ("Invoice Details", {
            "fields": [
                "order",
                "date_started",
                "date_completed",
                "terms",
                "description",
                "percent_of_performance_completed",
                "invoice_type",
                "attention",
                "mark_as_paid",
            ]
        }),
        ("Timestamps", {
            "fields": ["created_on", "updated_at"],
        }),
    ]


class InvoiceTransactionAdmin(admin.ModelAdmin):
    """
    Admin page for managing Invoice Transactions.
    """
    list_display = ["id", "invoice", "amount", "payment_date", "payment_no", "payment_desc", "created_on"]
    search_fields = ["id", "payment_no"]
    list_filter = ["payment_date", "created_on"]
    readonly_fields = ["created_on", "updated_at"]


class AccountSummaryAdmin(admin.ModelAdmin):
    """
    Admin page for managing Account Summaries.
    """
    list_display = ["id", "customer", "statement_no", "total", "attention", "created_by", "created_on"]
    search_fields = ["id", "statement_no"]
    list_filter = ["created_on"]
    readonly_fields = ["created_on", "updated_at"]


class InvoiceHistoryAdmin(admin.ModelAdmin):
    """
    Admin page for managing Invoice Histories.
    """
    list_display = ["id", "invoice", "total_invoiced", "total_paid", "balance_due", "pdf_filename", "created_on"]
    search_fields = ["id", "invoice__invoice_number", "pdf_filename"]
    list_filter = ["created_on"]
    readonly_fields = ["created_on", "updated_at"]


admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceTransaction, InvoiceTransactionAdmin)
admin.site.register(AccountSummary, AccountSummaryAdmin)
admin.site.register(InvoiceHistory, InvoiceHistoryAdmin)
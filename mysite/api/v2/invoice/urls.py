from django.urls import path

from .views import (
    InvoiceListView,
    InvoiceUpdateView,
    InvoiceDetailView,
    InvoiceArchiveView,
    InvoiceDeleteView,
    InvoiceCreateView,
    InvoiceHistoryListView,
    InvoiceOrderListView,
    InvoiceTransactionCreateView,
    InvoiceTransactionUpdateView,
    InvoiceTransactionListView,
    InvoiceTransactionDeleteView,
    MassPaymentView,
)


urlpatterns = [
    path(
        "invoice/get/",
        InvoiceListView.as_view(),
        name="invoice-list"
    ),
    path(
        "invoice/detail/<int:invoice_id>/",
        InvoiceDetailView.as_view(),
        name="invoice-detail",
    ),
    path(
        "invoice/create/",
        InvoiceCreateView.as_view(),
        name="invoice-create"
    ),
    path(
        "invoice/order/<int:order_id>/",
        InvoiceOrderListView.as_view(),
        name="invoice-order-by-order_id",
    ),
    # path(
    #     "invoice/order/",
    #     InvoiceOrderListView.as_view(),
    #     name="invoice-order",
    # ),
    path(
        "invoice/update/<int:invoice_id>/",
        InvoiceUpdateView.as_view(),
        name="invoice-update",
    ),
    path(
        "invoice/delete/<int:id>/",
        InvoiceDeleteView.as_view(),
        name="invoice-delete"
    ),
    path(
        "invoice/archive/<int:id>/",
        InvoiceArchiveView.as_view(),
        name="invoice-archive",
    ),
    path(
        "invoice/transaction/create/",
        InvoiceTransactionCreateView.as_view(),
        name="invoice-transaction-create",
    ),
    path(
        "invoice/transaction/update/<int:transaction_id>/",
        InvoiceTransactionUpdateView.as_view(),
        name="invoice-transaction-update",
    ),
    path(
        "invoice/transactions/<int:invoice_id>/",
        InvoiceTransactionListView.as_view(),
        name="invoice-transaction-list",
    ),
    path(
        "invoice/transaction/delete/<int:invoice_id>/",
        InvoiceTransactionDeleteView.as_view(),
        name="invoice-payment-delete",
    ),
    path(
        "invoice/histories/<int:invoice_id>/",
        InvoiceHistoryListView.as_view(),
        name="invoice-history-list",
    ),
    path(
        "invoice/mass-payment/<int:company_id>/",
        MassPaymentView.as_view(),
        name="invoice-mass-payment",
    ),
]

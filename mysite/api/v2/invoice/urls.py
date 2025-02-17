from django.urls import path

from .views import (
    InvoiceListView,
    InvoiceUpdateView,
    InvoiceDetailView,
    InvoiceArchiveView,
    InvoiceDeleteView,
    InvoiceCreateView,
    InvoicePaymentView,
    InvoicePaymentDeleteView,
    InvoiceHistoryListView,
    InvoiceOrderListView,
)


urlpatterns = [
    path('invoice/get/',
         InvoiceListView.as_view(),
         name='invoice-list'
         ),
    path('invoice/create/',
         InvoiceCreateView.as_view(),
         name='invoice-create'
         ),
    path(
        "invoice/order/<int:order_id>/",
        InvoiceOrderListView.as_view(),
        name="invoice-order-by-order_id",
    ),
    path(
        "invoice/order/",
        InvoiceOrderListView.as_view(),
        name="invoice-order",
    ),
    path('invoice/update/<int:invoice_id>/',
         InvoiceUpdateView.as_view(),
         name='invoice-update'
         ),
    path('invoice/detail/<int:invoice_id>/',
         InvoiceDetailView.as_view(),
         name='invoice-detail'
         ),
    path('invoice/delete/<int:id>/',
         InvoiceDeleteView.as_view(),
         name='invoice-delete'
         ),
    path('invoice/archive/<int:id>/',
         InvoiceArchiveView.as_view(),
         name='invoice-archive'
         ),
    path('invoice/payment/get/<int:invoice_id>/',
         InvoicePaymentView.as_view(),
         name='invoice-payment-get'
         ),
    path('invoice/payment/delete/<int:invoice_id>/',
         InvoicePaymentDeleteView.as_view(),
         name='invoice-payment-delete'
         ),
    path('invoice/history/get/<int:invoice_id>/',
         InvoiceHistoryListView.as_view(),
         name='invoice-history-get'
         ),
]

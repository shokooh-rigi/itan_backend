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
    AccountSummaryAPIView,
    AccountSummaryDeleteView,
    AccountSummaryCreateView,
    AccountSummaryListView,
    InvoiceOrderListView,
)


urlpatterns = [
    path('invoice/summary/',
         AccountSummaryAPIView.as_view(),
         name='invoice-summary'
         ),
    path('account/summary/create/<int:customer_id>/',
         AccountSummaryCreateView.as_view(),
         name='account-summary-create'
         ),
    path('account/summary/delete/<int:account_summary_id>/',
         AccountSummaryDeleteView.as_view(),
         name='account-summary-delete'
         ),
    path('account/summary/list/',
         AccountSummaryListView.as_view(),
         name='account-summary-list'
         ),
]

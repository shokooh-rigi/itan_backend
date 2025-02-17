from django.urls import path

from .views import (
    AccountSummaryAPIView,
    AccountSummaryDeleteView,
    AccountSummaryCreateView,
    AccountSummaryListView,
)


urlpatterns = [
    path('account-summary/',
         AccountSummaryAPIView.as_view(),
         name='invoice-summary'
         ),
    path('account-summary/create/<int:customer_id>/',
         AccountSummaryCreateView.as_view(),
         name='account-summary-create'
         ),
    path('account-summary/delete/<int:account_summary_id>/',
         AccountSummaryDeleteView.as_view(),
         name='account-summary-delete'
         ),
    path('account-summary/list/',
         AccountSummaryListView.as_view(),
         name='account-summary-list'
         ),
]

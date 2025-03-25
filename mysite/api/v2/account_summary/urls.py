from django.urls import path

from .views import (
    AccountSummaryCreateView,
    AccountSummaryListView,
)


urlpatterns = [

    path('account-summary/create/<int:customer_id>/',
         AccountSummaryCreateView.as_view(),
         name='account-summary-create'
         ),

    path('account-summary/list/',
         AccountSummaryListView.as_view(),
         name='account-summary-list'
         ),
]

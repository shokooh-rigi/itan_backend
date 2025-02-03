from django.urls import path
from .views import SettlementListView

urlpatterns = [
    path('settlements/', SettlementListView.as_view(), name='settlement-list'),
]

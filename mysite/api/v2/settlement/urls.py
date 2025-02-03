from django.urls import path
from .views import SettlementListView, SettlementCreateView, SettlementDeleteView

urlpatterns = [
    path('settlement/list/', SettlementListView.as_view(), name='settlement-list'),
    path('settlement/create/', SettlementCreateView.as_view(), name='settlement-create'),
    path('settlement/<int:pk>/delete/', SettlementDeleteView.as_view(), name='settlement-delete'),
]

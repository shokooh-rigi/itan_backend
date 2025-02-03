from django.urls import path
from .views import SettlementListView, SettlementCreateView

urlpatterns = [
    path('settlement/list/', SettlementListView.as_view(), name='settlement-list'),
    path('settlement/create/', SettlementCreateView.as_view(), name='settlement-create'),

]

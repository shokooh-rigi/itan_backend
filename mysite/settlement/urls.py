from django.urls import path

from .views import *

urlpatterns = [
    path('settlement/', settlement_list, name='settlementHome'),
    path('settlement/add/', settlement_add, name='settlementAdd'),
    path('settlement/view/<int:settlement_id>/', settlement_view, name='settlementView'),
    path('settlement/orders/<int:settlement_id>/', settlement_orders, name='settlementOrders'),
    path('settlement/edit/<int:settlement_id>/', settlement_edit, name='settlementEdit'),
    path('settlement/delete/<int:settlement_id>/', settlement_delete, name='settlementDelete'),
    path('settlement/generate_pdf/<int:settlement_id>/', generate_pdf, name='generateSettlementPDF'),
    # path('settlement/delete-settled-order/<int:settlement_id>/<int:settled_order_id>/', settled_order_delete,
    #      name='settledOrderDelete'),
]

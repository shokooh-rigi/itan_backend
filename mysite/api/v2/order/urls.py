from django.urls import path
from .views import OrderListAPIView, OrderAddAPIView, OrderEditAPIView, OrderDeleteAPIView, OrderArchiveAPIView

urlpatterns = [
    path('orders/', OrderListAPIView.as_view(), name='order-list'),
    path('orders/add/', OrderAddAPIView.as_view(), name='order-add'),
    path('orders/<int:order_id>/edit/', OrderEditAPIView.as_view(), name='order-edit'),
 path('orders/<int:order_id>/delete/', OrderDeleteAPIView.as_view(), name='order-delete'),
    path('orders/<int:order_id>/archive/', OrderArchiveAPIView.as_view(), name='order-archive'),
]

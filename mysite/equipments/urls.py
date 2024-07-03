from django.urls import path
from .views import order_update, equipment_update

urlpatterns = [
    path('order/update/<int:order_id>/', order_update, name='order_update_new'),
    path('update/<int:equipment_id>/', equipment_update, name='equipment_update'),
]

from django.urls import path
from .views import (
    order_update, equipment_update, equipment_forms_update,
    terminals_update
)

urlpatterns = [
    path('order/update/<int:order_id>/', order_update, name='order_update_new'),
    path('update/<int:equipment_id>/', equipment_update, name='equipment_update'),
    path('update/<int:equipment_id>/forms', equipment_forms_update, name='equipment_forms_update'),
    path('terminals/<int:datasheet_id>/update/', terminals_update, name='terminals_update'),
]

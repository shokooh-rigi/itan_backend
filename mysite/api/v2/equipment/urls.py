from django.urls import path

from mysite.api.v2.equipment.views import (
    EquipmentListView,
    EquipmentCreateView,
    EquipmentUpdateView,
    EquipmentDeleteView,
)


urlpatterns = [
    path(
        'equipment/',
        EquipmentListView.as_view(),
        name='equipment-list'
    ),
    path(
        'equipment/create/',
        EquipmentCreateView.as_view(),
        name='equipment-create'
    ),
    path(
        'equipment/<int:pk>/update/',
        EquipmentUpdateView.as_view(),
        name='equipment-update'
    ),
    path(
        'equipment/<int:pk>/delete/',
        EquipmentDeleteView.as_view(),
        name='equipment-delete'
    ),
]

from django.urls import path

from mysite.dbmanagement import views

urlpatterns = [
    path('equipments/', views.equipment_db, name='EquipmentsHome'),
    path('equipments/new/', views.equipment_create, name='EquipmentsCreate'),
    path('equipments/edit/<int:equipment_id>/', views.equipment_edit, name='EquipmentsEdit'),
    path('equipments/equipment-submittal/<int:equipment_id>/', views.equipment_submittal, name='EquipmentsEquipmentSubmittal'),
    path('equipments/equipment-image/<int:equipment_id>/', views.equipment_image, name='EquipmentsImage'),
    path('equipments/values/<int:equipment_id>/', views.equipment_values, name='EquipmentsValues'),
    path('vavequipments/values/<int:equipment_id>/', views.vav_equipment_values, name='VavEquipmentsValues'),
    path('equipments/get_values/<equipment_id>/', views.get_equipment_values, name='EquipmentsGetValues'),
    path('equipments/delete/<int:equipment_id>/', views.equipment_delete, name='EquipmentsDelete'),
    path('manufacturer/create/', views.manufacturer_create_popup, name="manufacturerCreate"),
    path('manufacturer/<int:pk>/edit/', views.manufacturer_edit_popup, name="manufacturerEdit"),
]

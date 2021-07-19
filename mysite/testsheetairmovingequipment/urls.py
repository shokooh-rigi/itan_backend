from django.urls import path
from . import views

urlpatterns = [
    path('air-moving-equipment/', views.air_moving_equipment_sheet_list, name='airMovingEquipmentSheetHome'),
    path('air-moving-equipment/add/', views.air_moving_equipment_sheet_add, name='airMovingEquipmentSheetAdd'),
    path('air-moving-equipment/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='airMovingEquipmentGenerateReportPDF'),
    path('air-moving-equipment/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='airMovingEquipmentGenerateTechPDF'),
    path('air-moving-equipment/equipments_list/<int:sheet_id>/', views.air_moving_equipment_sheet_equipment_list, name='airMovingEquipmentSheetEquipmentList'),
    path('air-moving-equipment/equipment_add/<int:sheet_id>/', views.air_moving_equipment_equipment_add, name='airMovingEquipmentEquipmentAdd'),
    path('air-moving-equipment/equipment_common_data/<int:air_moving_equipment_equipment_id>/', views.air_moving_equipment_common_data, name='airMovingEquipmentCommonData'),
    path('air-moving-equipment/equipment_design_value/<int:air_moving_equipment_equipment_id>/', views.air_moving_equipment_design_data, name='airMovingEquipmentDesignData'),
    path('air-moving-equipment/equipment_actual_value/<int:air_moving_equipment_equipment_id>/', views.air_moving_equipment_actual_data, name='airMovingEquipmentActualData'),
    path('air-moving-equipment/delete/<int:sheet_id>/', views.air_moving_equipment_sheet_delete, name='airMovingEquipmentSheetDelete'),
]

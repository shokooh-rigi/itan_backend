from django.urls import path
from . import views

urlpatterns = [
    path('pump/', views.pump_sheet_list, name='pumpSheetHome'),
    path('pump/add/', views.pump_sheet_add, name='pumpSheetAdd'),
    path('pump/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='pumpGenerateReportPDF'),
    path('pump/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='pumpGenerateTechPDF'),
    path('pump/equipments_list/<int:sheet_id>/', views.pump_sheet_equipment_list, name='pumpSheetEquipmentList'),
    path('pump/equipment_add/<int:sheet_id>/', views.pump_equipment_add, name='pumpEquipmentAdd'),
    path('pump/equipment_common_data/<int:pump_equipment_id>/', views.pump_common_data, name='pumpCommonData'),
    path('pump/equipment_design_value/<int:pump_equipment_id>/', views.pump_design_data, name='pumpDesignData'),
    path('pump/equipment_actual_value/<int:pump_equipment_id>/', views.pump_actual_data, name='pumpActualData'),
    path('pump/delete/<int:sheet_id>/', views.pump_sheet_delete, name='pumpSheetDelete'),
]

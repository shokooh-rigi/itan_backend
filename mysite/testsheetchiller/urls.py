from django.urls import path
from . import views

urlpatterns = [
    path('chiller/', views.chiller_sheet_list, name='chillerSheetHome'),
    path('chiller/add/', views.chiller_sheet_add, name='chillerSheetAdd'),
    path('chiller/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='chillerGenerateReportPDF'),
    path('chiller/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='chillerGenerateTechPDF'),
    path('chiller/equipments_list/<int:sheet_id>/', views.chiller_sheet_equipment_list, name='chillerSheetEquipmentList'),
    path('chiller/equipment_add/<int:sheet_id>/', views.chiller_equipment_add, name='chillerEquipmentAdd'),
    path('chiller/equipment_common_data/<int:chiller_equipment_id>/', views.chiller_common_data, name='chillerCommonData'),
    path('chiller/equipment_design_value/<int:chiller_equipment_id>/', views.chiller_design_data, name='chillerDesignData'),
    path('chiller/equipment_actual_value/<int:chiller_equipment_id>/', views.chiller_actual_data, name='chillerActualData'),
    path('chiller/delete/<int:sheet_id>/', views.chiller_sheet_delete, name='chillerSheetDelete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('vbfhs/', views.vbfhs_sheet_list, name='vbfhsSheetHome'),
    path('vbfhs/add/', views.vbfhs_sheet_add, name='vbfhsSheetAdd'),
    path('vbfhs/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='vbfhsGenerateReportPDF'),
    path('vbfhs/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='vbfhsGenerateTechPDF'),
    path('vbfhs/equipments_list/<int:sheet_id>/', views.vbfhs_sheet_equipment_list, name='vbfhsSheetEquipmentList'),
    path('vbfhs/equipment_add/<int:sheet_id>/', views.vbfhs_equipment_add, name='vbfhsEquipmentAdd'),
    path('vbfhs/equipment_design_value/<int:vbfhs_equipment_id>/', views.vbfhs_design_data, name='vbfhsDesignData'),
    path('vbfhs/equipment_actual_value/<int:vbfhs_equipment_id>/', views.vbfhs_actual_data, name='vbfhsActualData'),
    path('vbfhs/delete/<int:sheet_id>/', views.vbfhs_sheet_delete, name='vbfhsSheetDelete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('induction_unit/', views.induction_unit_sheet_list, name='inductionUnitSheetHome'),
    path('induction_unit/add/', views.induction_unit_sheet_add, name='inductionUnitSheetAdd'),
    path('induction_unit/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='inductionUnitGenerateReportPDF'),
    path('induction_unit/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='inductionUnitGenerateTechPDF'),
    path('induction_unit/equipments_list/<int:sheet_id>/', views.induction_unit_sheet_equipment_list, name='inductionUnitSheetEquipmentList'),
    path('induction_unit/equipment_add/<int:sheet_id>/', views.induction_unit_equipment_add, name='inductionUnitEquipmentAdd'),
    path('induction_unit/equipment_design_value/<int:induction_unit_equipment_id>/', views.induction_unit_design_data, name='inductionUnitDesignData'),
    path('induction_unit/equipment_actual_value/<int:induction_unit_equipment_id>/', views.induction_unit_actual_data, name='inductionUnitActualData'),
    path('induction_unit/delete/<int:sheet_id>/', views.induction_unit_sheet_delete, name='inductionUnitSheetDelete'),
]

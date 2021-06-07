from django.urls import path
from . import views

urlpatterns = [
    path('duct/', views.duct_sheet_list, name='ductSheetHome'),
    path('duct/add/', views.duct_sheet_add, name='ductSheetAdd'),
    path('duct/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='ductGenerateReportPDF'),
    path('duct/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='ductGenerateTechPDF'),
    path('duct/equipments_list/<int:sheet_id>/', views.duct_sheet_equipment_list, name='ductSheetEquipmentList'),
    path('duct/equipment_add/<int:sheet_id>/', views.duct_equipment_add, name='ductEquipmentAdd'),
    path('duct/equipment_design_value/<int:duct_equipment_id>/', views.duct_design_data, name='ductDesignData'),
    path('duct/equipment_actual_value/<int:duct_equipment_id>/', views.duct_actual_data, name='ductActualData'),
    path('duct/delete/<int:sheet_id>/', views.duct_sheet_delete, name='ductSheetDelete'),
]

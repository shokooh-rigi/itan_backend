from django.urls import path
from . import views

urlpatterns = [
    path('dalt/', views.dalt_sheet_list, name='daltSheetHome'),
    path('dalt/add/', views.dalt_sheet_add, name='daltSheetAdd'),
    path('dalt/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='daltGenerateReportPDF'),
    path('dalt/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='daltGenerateTechPDF'),
    path('dalt/equipments_list/<int:sheet_id>/', views.dalt_sheet_equipment_list, name='daltSheetEquipmentList'),
    path('dalt/equipment_add/<int:sheet_id>/', views.dalt_equipment_add, name='daltEquipmentAdd'),
    path('dalt/equipment_design_value/<int:dalt_equipment_id>/', views.dalt_design_data, name='daltDesignData'),
    path('dalt/equipment_actual_value/<int:dalt_equipment_id>/', views.dalt_actual_data, name='daltActualData'),
    path('dalt/delete/<int:sheet_id>/', views.dalt_sheet_delete, name='daltSheetDelete'),
]

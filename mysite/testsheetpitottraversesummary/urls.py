from django.urls import path
from . import views

urlpatterns = [
    path('', views.pitot_traverse_summary_sheet_list, name='pitotTraverseSummarySheetHome'),
    path('add/', views.pitot_traverse_summary_sheet_add, name='pitotTraverseSummarySheetAdd'),
    path('equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='pitotTraverseSummaryGenerateReportPDF'),
    path('equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='pitotTraverseSummaryGenerateTechPDF'),
    path('equipments_list/<int:sheet_id>/', views.pitot_traverse_summary_sheet_equipment_list, name='pitotTraverseSummarySheetEquipmentList'),
    path('equipment_add/<int:sheet_id>/', views.pitot_traverse_summary_equipment_add, name='pitotTraverseSummaryEquipmentAdd'),
    path('equipment_design_value/<int:equipment_id>/', views.pitot_traverse_summary_design_data, name='pitotTraverseSummaryDesignData'),
    path('equipment_actual_value/<int:equipment_id>/', views.pitot_traverse_summary_actual_data, name='pitotTraverseSummaryActualData'),
    path('delete/<int:sheet_id>/', views.pitot_traverse_summary_sheet_delete, name='pitotTraverseSummarySheetDelete'),
]

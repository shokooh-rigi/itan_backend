from django.urls import path
from . import views

urlpatterns = [
    path('velocity/', views.velocity_sheet_list, name='velocitySheetHome'),
    path('velocity/add/', views.velocity_sheet_add, name='velocitySheetAdd'),
    path('velocity/equipment_add/<int:sheet_id>/', views.velocity_equipment_add, name='velocityEquipmentAdd'),
    path('velocity/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='velocityGenerateTechPDF'),
    path('velocity/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='velocityGenerateReportPDF'),
    path('velocity/equipments_list/<int:sheet_id>/', views.velocity_sheet_equipment_list, name='velocitySheetEquipmentList'),
    # path('velocity/equipment_design_data/<int:sheet_id>/<int:sheet_equipment_id>/', views.velocity_sheet_equipment_design_data, name='velocitySheetEquipmentDesignData'),
    path('velocity/equipment_actual_value/<int:sheet_id>/<int:sheet_equipment_id>/', views.velocity_actual_data, name='velocityActualData'),
    path('velocity/delete/<int:sheet_id>/', views.velocity_sheet_delete, name='velocitySheetDelete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('terminal/', views.terminal_sheet_list, name='terminalSheetHome'),
    path('terminal/add/', views.terminal_sheet_add, name='terminalSheetAdd'),
    path('terminal/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='terminalSheetEquipmentsGenerateTechPDF'),
    path('terminal/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='terminalSheetEquipmentsGenerateReportPDF'),
    path('terminal/equipments_list/<int:sheet_id>/', views.terminal_sheet_equipment_list, name='terminalSheetEquipmentList'),
    path('terminal/equipment_design_data/<int:sheet_equipment_id>/', views.terminal_sheet_equipment_design_data, name='terminalSheetEquipmentDesignData'),
    path('terminal/equipment_actual_value/<int:sheet_equipment_id>/', views.terminal_sheet_equipment_actual_data, name='terminalSheetEquipmentActualData'),
    path('terminal/delete/<int:sheet_id>/', views.vav_sheet_delete, name='terminalSheetDelete'),
    path('terminal/delete/<int:sheet_id>/<str:sheet_equipment_name>/', views.vav_sheet_equipment_delete, name='terminalSheetEquipmentDelete'),
]

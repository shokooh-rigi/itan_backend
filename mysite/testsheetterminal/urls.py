from django.urls import path
from . import views

urlpatterns = [
    path('terminal/', views.terminal_sheet_list, name='terminalSheetHome'),
    path('terminal/add/', views.terminal_sheet_add, name='terminalSheetAdd'),
    path('terminal/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='TerminalGenerateTechPDF'),
    path('terminal/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='TerminalGenerateReportPDF'),
    path('terminal/equipments_list/<int:sheet_id>/', views.terminal_sheet_equipment_list, name='terminalSheetEquipmentList'),
    path('terminal/other_terminals/<int:sheet_id>/', views.terminal_sheet_others, name='terminalSheetOthers'),
    path('terminal/equipment_design_data/<int:sheet_id>/<int:sheet_equipment_id>/', views.terminal_sheet_equipment_design_data, name='terminalSheetEquipmentDesignData'),
    path('terminal/rogue_design_data/<int:sheet_id>/', views.rogue_design_data, name='rogueDesignData'),
    path('terminal/equipment_actual_value/<int:sheet_id>/<int:sheet_equipment_id>/', views.terminal_sheet_equipment_actual_data, name='terminalSheetEquipmentActualData'),
    path('terminal/rogue_actual_data/<int:sheet_id>/', views.rogue_actual_data, name='rogueActualData'),
    path('terminal/delete/<int:sheet_id>/', views.terminal_sheet_delete, name='terminalSheetDelete'),
]

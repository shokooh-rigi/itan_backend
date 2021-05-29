from django.urls import path
from . import views

urlpatterns = [
    path('flow/', views.flow_sheet_list, name='flowSheetHome'),
    path('flow/add/', views.flow_sheet_add, name='flowSheetAdd'),
    path('flow/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='flowGenerateReportPDF'),
    path('flow/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='flowGenerateTechPDF'),
    path('flow/equipments_list/<int:sheet_id>/', views.flow_sheet_equipment_list, name='flowSheetEquipmentList'),
    path('flow/equipment_add/<int:sheet_id>/', views.flow_equipment_add, name='flowEquipmentAdd'),
    path('flow/equipment_common_data/<int:flow_equipment_id>/', views.flow_common_data, name='flowCommonData'),
    path('flow/equipment_design_value/<int:flow_equipment_id>/', views.flow_design_data, name='flowDesignData'),
    path('flow/equipment_actual_value/<int:flow_equipment_id>/', views.flow_actual_data, name='flowActualData'),
    path('flow/delete/<int:sheet_id>/', views.flow_sheet_delete, name='flowSheetDelete'),
]

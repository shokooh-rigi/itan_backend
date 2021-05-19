from django.urls import path
from . import views

urlpatterns = [
    path('flow/', views.flow_sheet_list, name='flowSheetHome'),
    path('flow/add/', views.flow_sheet_add, name='flowSheetAdd'),
    path('flow/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='flowGenerateReportPDF'),
    path('flow/equipments_list/<int:sheet_id>/', views.velocity_sheet_equipment_list, name='flowSheetEquipmentList'),
    path('flow/equipment_actual_value/<int:sheet_id>/<int:sheet_equipment_id>/', views.velocity_actual_data, name='flowActualData'),
    path('flow/delete/<int:sheet_id>/', views.flow_sheet_delete, name='flowSheetDelete'),
]

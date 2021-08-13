from django.urls import path
from . import views

urlpatterns = [
    path('', views.sheet_list, name='vbtsSheetHome'),
    path('add/', views.sheet_add, name='vbtsSheetAdd'),
    path('equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='vbtsGenerateReportPDF'),
    path('equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='vbtsGenerateTechPDF'),
    path('equipments_list/<int:sheet_id>/', views.sheet_equipment_list, name='vbtsSheetEquipmentList'),
    path('equipment_add/<int:sheet_id>/', views.equipment_add, name='vbtsEquipmentAdd'),
    path('equipment_design_value/<int:equipment_id>/', views.design_data, name='vbtsDesignData'),
    path('equipment_actual_value/<int:equipment_id>/', views.actual_data, name='vbtsActualData'),
    path('delete/<int:sheet_id>/', views.sheet_delete, name='vbtsSheetDelete'),
]

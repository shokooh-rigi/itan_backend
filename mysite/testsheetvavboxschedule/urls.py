from django.urls import path
from . import views

urlpatterns = [
    path('', views.sheet_list, name='vbsSheetHome'),
    path('add/', views.sheet_add, name='vbsSheetAdd'),
    path('equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='vbsGenerateReportPDF'),
    path('equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='vbsGenerateTechPDF'),
    path('equipments_list/<int:sheet_id>/', views.sheet_equipment_list, name='vbsSheetEquipmentList'),
    path('equipment_add/<int:sheet_id>/', views.equipment_add, name='vbsEquipmentAdd'),
    path('equipment_common_value/<int:equipment_id>/', views.common_data, name='vbsCommonData'),
    path('equipment_design_value/<int:equipment_id>/', views.design_data, name='vbsDesignData'),
    path('equipment_actual_value/<int:equipment_id>/', views.actual_data, name='vbsActualData'),
    path('delete/<int:sheet_id>/', views.sheet_delete, name='vbsSheetDelete'),
]

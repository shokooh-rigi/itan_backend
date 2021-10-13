from django.urls import path
from . import views

urlpatterns = [
    path('', views.hot_water_boiler_sheet_list, name='hotWaterBoilerSheetHome'),
    path('add/', views.hot_water_boiler_sheet_add, name='hotWaterBoilerSheetAdd'),
    path('equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='hotWaterBoilerGenerateReportPDF'),
    path('equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='hotWaterBoilerGenerateTechPDF'),
    path('equipments_list/<int:sheet_id>/', views.hot_water_boiler_sheet_equipment_list, name='hotWaterBoilerSheetEquipmentList'),
    path('equipment_add/<int:sheet_id>/', views.hot_water_boiler_equipment_add, name='hotWaterBoilerEquipmentAdd'),
    path('equipment_common_data/<int:equipment_id>/', views.hot_water_boiler_common_data, name='hotWaterBoilerCommonData'),
    path('equipment_design_value/<int:equipment_id>/', views.hot_water_boiler_design_data, name='hotWaterBoilerDesignData'),
    path('equipment_actual_value/<int:equipment_id>/', views.hot_water_boiler_actual_data, name='hotWaterBoilerActualData'),
    path('delete/<int:sheet_id>/', views.hot_water_boiler_sheet_delete, name='hotWaterBoilerSheetDelete'),
]

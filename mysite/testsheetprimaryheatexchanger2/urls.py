from django.urls import path
from . import views

urlpatterns = [
    path('', views.primary_heat_exchanger_2_sheet_list, name='primaryHeatExchanger2SheetHome'),
    path('add/', views.primary_heat_exchanger_2_sheet_add, name='primaryHeatExchanger2SheetAdd'),
    path('equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='primaryHeatExchanger2GenerateReportPDF'),
    path('equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='primaryHeatExchanger2GenerateTechPDF'),
    path('equipments_list/<int:sheet_id>/', views.primary_heat_exchanger_2_sheet_equipment_list, name='primaryHeatExchanger2SheetEquipmentList'),
    path('equipment_add/<int:sheet_id>/', views.primary_heat_exchanger_2_equipment_add, name='primaryHeatExchanger2EquipmentAdd'),
    path('equipment_common_data/<int:equipment_id>/', views.primary_heat_exchanger_2_common_data, name='primaryHeatExchanger2CommonData'),
    path('equipment_design_value/<int:equipment_id>/', views.primary_heat_exchanger_2_design_data, name='primaryHeatExchanger2DesignData'),
    path('equipment_actual_value/<int:equipment_id>/', views.primary_heat_exchanger_2_actual_data, name='primaryHeatExchanger2ActualData'),
    path('delete/<int:sheet_id>/', views.primary_heat_exchanger_2_sheet_delete, name='primaryHeatExchanger2SheetDelete'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('primary-heat-exchanger/', views.primary_heat_exchanger_sheet_list, name='primaryHeatExchangerSheetHome'),
    path('primary-heat-exchanger/add/', views.primary_heat_exchanger_sheet_add, name='primaryHeatExchangerSheetAdd'),
    path('primary-heat-exchanger/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='primaryHeatExchangerGenerateReportPDF'),
    path('primary-heat-exchanger/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='primaryHeatExchangerGenerateTechPDF'),
    path('primary-heat-exchanger/equipments_list/<int:sheet_id>/', views.primary_heat_exchanger_sheet_equipment_list, name='primaryHeatExchangerSheetEquipmentList'),
    path('primary-heat-exchanger/equipment_add/<int:sheet_id>/', views.primary_heat_exchanger_equipment_add, name='primaryHeatExchangerEquipmentAdd'),
    path('primary-heat-exchanger/equipment_common_data/<int:primary_heat_exchanger_equipment_id>/', views.primary_heat_exchanger_common_data, name='primaryHeatExchangerCommonData'),
    path('primary-heat-exchanger/equipment_design_value/<int:primary_heat_exchanger_equipment_id>/', views.primary_heat_exchanger_design_data, name='primaryHeatExchangerDesignData'),
    path('primary-heat-exchanger/equipment_actual_value/<int:primary_heat_exchanger_equipment_id>/', views.primary_heat_exchanger_actual_data, name='primaryHeatExchangerActualData'),
    path('primary-heat-exchanger/delete/<int:sheet_id>/', views.primary_heat_exchanger_sheet_delete, name='primaryHeatExchangerSheetDelete'),
]

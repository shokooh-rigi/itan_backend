from django.urls import path
from . import views

urlpatterns = [
    path('vav/', views.vav_sheet_list, name='vavSheetHome'),
    # path('sheetcreator/equipments_list/<int:sheet_id>/', views.equipments_list, name='sheetEquipmentsList'),
    # path('sheetcreator/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='sheetEquipmentsGenerateTechPDF'),
    # path('sheetcreator/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='sheetEquipmentsGenerateReportPDF'),
    path('vav/add/', views.vav_sheet_add, name='vavSheetAdd'),
    path('vav/equipments/<int:sheet_id>/', views.vav_sheet_equipment, name='vavSheetEquipment'),
    path('vav/equipments_list/<int:sheet_id>/', views.vav_sheet_equipment_list, name='vavSheetEquipmentList'),
    path('vav/equipment_general_data/<int:sheet_equipment_id>/', views.vav_sheet_equipment_general_data, name='vavSheetEquipmentGeneralData'),
    path('vav/equipment_design_data/<int:sheet_equipment_id>/', views.vav_sheet_equipment_design_data, name='vavSheetEquipmentDesignData'),
    path('vav/equipment_actual_value/<int:sheet_equipment_id>/', views.vav_sheet_equipment_actual_data, name='vavSheetEquipmentActualData'),
    # path('order/edit/<int:order_id>/', views.order_edit, name='orderEdit'),
    # path('order/archive/<int:order_id>/', views.order_archive, name='orderArchive'),
    path('vav/delete/<int:sheet_id>/', views.vav_sheet_delete, name='vavSheetDelete'),
    path('vav/delete/<int:sheet_id>/<str:sheet_equipment_name>/', views.vav_sheet_equipment_delete, name='vavSheetEquipmentDelete'),
    # path('order/change-order/<int:order_id>/', views.change_order, name='changeOrder'),
    # path('order/remove-change-order/<int:order_id>/<int:change_order_id>/', views.change_order_delete,
    #      name='deleteChangeOrder'),
]

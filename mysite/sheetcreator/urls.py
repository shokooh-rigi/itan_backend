from django.urls import path

from mysite.sheetcreator import views

urlpatterns = [
    path('sheetcreator/', views.sheet_list, name='sheetHome'),
    path('sheetcreator/equipments_list/<int:sheet_id>/', views.equipments_list, name='sheetEquipmentsList'),
    path('sheetcreator/equipments_generate_tech_pdf/<int:sheet_id>/', views.equipments_generate_tech_pdf, name='sheetEquipmentsGenerateTechPDF'),
    path('sheetcreator/equipments_generate_report_pdf/<int:sheet_id>/', views.equipments_generate_report_pdf, name='sheetEquipmentsGenerateReportPDF'),
    path('sheetcreator/add/', views.sheet_add, name='sheetAdd'),
    path('sheetcreator/equipments/<int:sheet_id>/', views.sheet_equipment, name='sheetEquipment'),
    path('sheetcreator/equipment_common_data/<int:sheet_equipment_id>/', views.sheet_equipment_common_data, name='sheetEquipmentCommonData'),
    path('sheetcreator/equipment_common_data_edit/<int:sheet_equipment_id>/', views.sheet_equipment_common_data_edit, name='sheetEquipmentCommonDataEdit'),
    path('sheetcreator/equipment_design_value/<int:sheet_equipment_id>/', views.review_equipment_values, name='sheetEquipmentDesignValue'),
    path('sheetcreator/equipment_actual_value/<int:sheet_equipment_id>/', views.equipment_actual_values, name='sheetEquipmentActualValue'),
    path('sheetcreator/equipment_actual_values_edit/<int:sheet_equipment_id>/', views.equipment_actual_values_edit, name='sheetEquipmentActualValueEdit'),
    # path('order/edit/<int:order_id>/', views.order_edit, name='orderEdit'),
    # path('order/archive/<int:order_id>/', views.order_archive, name='orderArchive'),
    path('sheetcreator/delete/<int:sheet_id>/', views.sheet_delete, name='sheetDelete'),
    path('sheetcreator/delete/<int:sheet_id>/<str:sheet_equipment_name>/', views.sheet_equipment_delete, name='sheetEquipmentDelete'),
    # path('order/change-order/<int:order_id>/', views.change_order, name='changeOrder'),
    # path('order/remove-change-order/<int:order_id>/<int:change_order_id>/', views.change_order_delete,
    #      name='deleteChangeOrder'),
]

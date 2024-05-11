from django.urls import path

from mysite.order import views

urlpatterns = [
    path('order/', views.order_list, name='orderHome'),
    path('order/add/', views.order_add, name='orderAdd'),
    path('order/add/<int:proposal_id>/', views.order_add, name='orderAddUsingProposal'),
    path('order/edit/<int:order_id>/', views.order_edit, name='orderEdit'),
    path('order/archive/<int:order_id>/', views.order_archive, name='orderArchive'),
    path('order/delete/<int:order_id>/', views.order_delete, name='orderDelete'),
    path('order/change-order/<int:order_id>/', views.change_order, name='changeOrder'),
    path('order/control-system/<int:order_id>/', views.control_system, name='controlSystem'),
    path('order/equipment-submittal/<int:order_id>/', views.order_equipment_submittal, name='equipmentSubmittal'),
    path('order/colored-drawing/<int:order_id>/', views.order_colored_drawing, name='coloredDrawing'),
    path('order/field_drawing/<int:order_id>/', views.order_field_drawing, name='fieldDrawing'),
    path('order/general_notes/<int:order_id>/', views.order_general_notes, name='generalNotes'),
    path('order/site-pictures/<int:order_id>/', views.order_site_pictures, name='sitePictures'),
    path('order/test-sheets/<int:order_id>/', views.order_test_sheets, name='testSheets'),
    path('order/remove-change-order/<int:order_id>/<int:change_order_id>/', views.change_order_delete, name='deleteChangeOrder'),
    path('order/approve-order/<int:change_order_id>/<int:action>/', views.approve_change_order, name='approveChangeOrder'),
    path('order/techlabel/<int:order_id>/', views.tech_label, name='techLabel'),
    path('controlsystem/create/', views.cs_create_popup, name="csCreate"),
    path('controlsystem/<int:pk>/edit/', views.cs_edit_popup, name="csEdit"),
    path('cs_manufacturer/create/', views.cs_manufacturer_create_popup, name="csManufacturerCreate"),
    path('manufacturer/<int:pk>/edit/', views.manufacturer_edit_popup, name="manufacturerEdit"),
    path('order/update/<int:order_id>/', views.order_uppdate, name="order_update"),
    path('order/update/<int:order_id>/delete-datasheet/<int:datasheet_id>/', views.delete_datasheet, name='delete_datasheet'),
]
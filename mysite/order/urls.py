from django.conf.urls import url
from django.urls import path

from mysite.order import views

urlpatterns = [
    path('order/', views.order_list, name='orderHome'),
    path('order/add/', views.order_add, name='orderAdd'),
    path('order/edit/<int:order_id>/', views.order_edit, name='orderEdit'),
    path('order/archive/<int:order_id>/', views.order_archive, name='orderArchive'),
    path('order/delete/<int:order_id>/', views.order_delete, name='orderDelete'),
    path('order/change-order/<int:order_id>/', views.change_order, name='changeOrder'),
    path('order/control-system/<int:order_id>/', views.control_system, name='controlSystem'),
    path('order/equipment-submittal/<int:order_id>/', views.order_equipment_submittal, name='equipmentSubmittal'),
    path('order/remove-change-order/<int:order_id>/<int:change_order_id>/', views.change_order_delete,
         name='deleteChangeOrder'),
    path('order/techlabel/<int:order_id>/', views.tech_label, name='techLabel'),
    url(r'^controlsystem/create', views.cs_create_popup, name="csCreate"),
    url(r'^controlsystem/(?P<pk>\d+)/edit', views.cs_edit_popup, name="csEdit"),
    url(r'^cs_manufacturer/create', views.cs_manufacturer_create_popup, name="csManufacturerCreate"),
    url(r'^manufacturer/(?P<pk>\d+)/edit', views.manufacturer_edit_popup, name="manufacturerEdit"),
]

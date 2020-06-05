from django.urls import path

from mysite.sheetcreator import views

urlpatterns = [
    path('sheetcreator/', views.sheet_list, name='sheetHome'),
    path('sheetcreator/add/', views.sheet_add, name='sheetAdd'),
    path('sheetcreator/equipments/<int:sheet_id>/', views.sheet_equipment, name='sheetEquipment'),
    # path('order/edit/<int:order_id>/', views.order_edit, name='orderEdit'),
    # path('order/archive/<int:order_id>/', views.order_archive, name='orderArchive'),
    # path('order/delete/<int:order_id>/', views.order_delete, name='orderDelete'),
    # path('order/change-order/<int:order_id>/', views.change_order, name='changeOrder'),
    # path('order/remove-change-order/<int:order_id>/<int:change_order_id>/', views.change_order_delete,
    #      name='deleteChangeOrder'),
]

from django.urls import path

from mysite.order import views

urlpatterns = [
    path('order/', views.order_list, name='orderHome'),
    path('order/add/', views.order_add, name='orderAdd'),
    path('order/edit/<int:order_id>/', views.order_edit, name='orderEdit'),
    path('order/archive/<int:order_id>/', views.order_archive, name='orderArchive'),
    path('order/delete/<int:order_id>/', views.order_delete, name='orderDelete'),
    path('order/change-order/<int:order_id>/', views.change_order, name='changeOrder'),
    path('order/remove-change-order/<int:order_id>/<int:change_order_id>/', views.change_order_delete,
         name='deleteChangeOrder'),
]

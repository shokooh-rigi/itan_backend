from django.urls import path

from mysite.gi import views

urlpatterns = [
    path('invoice/', views.invoice_list, name='invoiceHome'),
    path('invoice/add/', views.invoice_add, name='invoiceAdd'),
    path('invoice/view/<int:invoice_id>/', views.invoice_view, name='invoiceView'),
    path('invoice/edit/<int:invoice_id>/', views.invoice_edit, name='invoiceEdit'),
    path('invoice/archive/<int:invoice_id>/', views.invoice_archive, name='invoiceArchive'),
    path('invoice/delete/<int:invoice_id>/', views.invoice_delete, name='invoiceDelete'),
]

from django.urls import path

from mysite.gi import views

urlpatterns = [
    path('invoice/', views.invoice_list, name='invoiceHome'),
    path('invoice/add/', views.invoice_add, name='invoiceAdd'),
    path('invoice/add/<int:order_id>/', views.invoice_add, name='invoiceAddUsingOrder'),
    path('invoice/view/<int:invoice_id>/', views.invoice_view, name='invoiceView'),
    path('invoice/edit/<int:invoice_id>/', views.invoice_edit, name='invoiceEdit'),
    path('invoice/archive/<int:invoice_id>/', views.invoice_archive, name='invoiceArchive'),
    path('invoice/delete/<int:invoice_id>/', views.invoice_delete, name='invoiceDelete'),
    path('invoice/payment/<int:invoice_id>/', views.invoice_payment, name='invoicePayment'),
    path('transaction/delete/<int:transaction_id>/', views.invoice_payment_delete, name='invoicePaymentDelete'),
    path('account_summary/', views.account_summary_list, name='accountSummaryHome'),
    path('account_summary/add/', views.account_summary_add, name='accountSummaryAdd'),
    path('account_summary/delete/<int:account_summary_id>/', views.accout_summary_delete, name='accountSummaryDelete'),
]

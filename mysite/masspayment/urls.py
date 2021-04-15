from django.urls import path
from . import views

urlpatterns = [
    path('customerlist/', views.customer_list, name='customerListHome'),
    path('massPayment/<int:contact_id>/', views.mass_payment, name='customerMassPayment'),
]

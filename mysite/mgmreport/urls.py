from django.urls import path
from django.views.generic import TemplateView

from mysite.mgmreport import views

urlpatterns = [
    path('mgmreport/', TemplateView.as_view(template_name="mgmreport.html"), name='MgmReport'),
    path('mgmreport/equipment/', views.equipments_list, name='EquipmentsList'),
    path('mgmreport/company/', views.company_list, name='CompanyList'),
    path('mgmreport/bids/', views.bids_list, name='BidsList'),
]

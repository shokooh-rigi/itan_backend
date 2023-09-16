from django.urls import path
from django.views.generic import TemplateView

from mysite.mgmreport import views

urlpatterns = [
    path('mgmreport/', TemplateView.as_view(template_name="mgmreport.html"), name='MgmReport'),
    path('mgmreport/equipment/', views.equipments_list, name='EquipmentsList'),
    path('mgmreport/company/', views.company_list, name='CompanyList'),
    path('mgmreport/bids/<str:bid_type>/', views.bids_list, name='BidsList'),
    path('mgmreport/detailed_orders/', views.detailed_orders_list, name='DetailedOrders'),
]

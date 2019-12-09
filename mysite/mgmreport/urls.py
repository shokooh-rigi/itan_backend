from django.urls import path
from django.conf.urls import url
from mysite.mgmreport import views
from django.views.generic import TemplateView

urlpatterns = [
    path('mgmreport/', TemplateView.as_view(template_name="mgmreport.html"), name='MgmReport'),
    path('mgmreport/equipment/', views.equipments_list, name='EquipmentsList'),
    path('mgmreport/company/', views.company_list, name='CompanyList'),
    path('mgmreport/projects/', views.projects_list, name='ProjectsList'),
]

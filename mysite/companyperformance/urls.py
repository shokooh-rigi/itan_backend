from django.urls import path
from django.views.generic import TemplateView

from mysite.companyperformance import views

urlpatterns = [
    path('company-performance/', views.performance_list, name='PerformanceList'),
]

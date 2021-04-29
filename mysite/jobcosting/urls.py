from django.urls import path
from django.views.generic import TemplateView

from mysite.jobcosting import views

urlpatterns = [
    path('jobcosting/', views.job_costing_list, name='JobCostingList'),
]

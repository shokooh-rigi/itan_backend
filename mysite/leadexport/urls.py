from django.urls import path
from django.views.generic import TemplateView

from mysite.leadexport import views

urlpatterns = [
    path('lead-export/', views.lead_export, name='LeadExport'),
]

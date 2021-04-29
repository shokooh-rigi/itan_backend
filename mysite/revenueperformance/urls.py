from django.urls import path
from django.views.generic import TemplateView

from mysite.revenueperformance import views

urlpatterns = [
    path('revenue-performance/', views.revenue_list, name='RevenueList'),
]

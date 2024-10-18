from django.urls import path
from . import views

urlpatterns = [
    path('reports/orders/<int:order_id>/', views.report_sheet_show, name='report_show'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('reportsheet/', views.report_sheet_list, name='reportSheetHome'),
    path('reportsheet/add/', views.report_sheet_add, name='reportSheetAdd'),
    path('reportsheet/drawing/<int:sheet_id>/', views.report_sheet_drawing, name='reportSheetDrawing'),
]

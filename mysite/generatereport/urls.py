from django.urls import path
from . import views

urlpatterns = [
    path('reportsheet/', views.report_sheet_list, name='reportSheetHome'),
    path('reportsheet/add/', views.report_sheet_add, name='reportSheetAdd'),
    path('reportsheet/edit/<int:sheet_id>/', views.report_sheet_edit, name='reportSheetEdit'),
    path('reportsheet/recreate/<int:sheet_id>/', views.report_sheet_recreate, name='reportSheetRecreate'),
    path('reportsheet/finalize/<int:sheet_id>/', views.report_sheet_finalize, name='reportSheetFinalize'),
    path('reportsheet/delete/<int:sheet_id>/', views.delete_report_sheet, name='reportSheetDelete'),
    # path('reportsheet/drawing/<int:sheet_id>/', views.report_sheet_drawing, name='reportSheetDrawing'),
    path('reports/orders/<int:order_id>/', views.report_sheet_show, name='report_show'),
]

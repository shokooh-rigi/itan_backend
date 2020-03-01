from django.urls import path
from mysite.report import views

urlpatterns = [
    path('report/', views.report_list, name='reportHome'),
    path('report/add/', views.report_add, name='reportAdd'),
    path('report/edit/<int:report_id>/', views.report_edit, name='reportEdit'),
    path('report/delete/<int:report_id>/', views.report_delete, name='reportDelete'),
]

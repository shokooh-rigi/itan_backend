from django.urls import path
from . import views

urlpatterns = [
    path('projectprocess/', views.project_process_list, name='projectProcessHome'),
    path('projectprocess/edit/<int:order_id>/<int:pre_demo>/', views.project_process_edit, name='projectProcessEdit'),
]

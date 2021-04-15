from django.urls import path

from mysite.techupload import views

urlpatterns = [
    path('techupload/', views.projects_list, name='techUploadHome'),
    path('techupload/<int:project_id>', views.techupload_edit, name='techUploadEdit'),
]

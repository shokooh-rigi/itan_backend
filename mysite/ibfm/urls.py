from django.urls import path
from django.conf.urls import url
from mysite.ibfm import views

urlpatterns = [
    path('ibfm/', views.bid_files_list, name='ibidFilesHome'),
    path('ibfm/add', views.bidfiles_add, name='ibidFilesAdd'),
    path('ibfm/edit/<int:bidfiles_id>', views.bidfiles_edit, name='ibidFilesEdit'),
    path('ibfm/archive/<int:bidfiles_id>/', views.bidfiles_archive, name='ibidFilesArchive'),
    path('ibfm/delete/<int:bidfiles_id>/', views.bidfiles_delete, name='ibidFilesDelete'),
]

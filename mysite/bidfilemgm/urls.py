from django.urls import path

from mysite.bidfilemgm import views

urlpatterns = [
    path('bfm/', views.bid_files_list, name='bidFilesHome'),
    path('bfm/add', views.bidfiles_add, name='bidFilesAdd'),
    path('bfm/edit/<int:bidfiles_id>', views.bidfiles_edit, name='bidFilesEdit'),
    path('bfm/archive/<int:bidfiles_id>/', views.bidfiles_archive, name='bidFilesArchive'),
    path('bfm/delete/<int:bidfiles_id>/', views.bidfiles_delete, name='bidFilesDelete'),
]

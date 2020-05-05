from django.urls import path

from mysite.administrative import views

urlpatterns = [
    path('administrative/', views.documents_list, name='administrativeHome'),
    path('administrative/add', views.documents_add, name='administrativeAdd'),
    path('administrative/edit/<int:document_id>', views.document_edit, name='administrativeEdit'),
    path('administrative/delete/<int:document_id>/', views.document_delete, name='administrativeDelete'),
]

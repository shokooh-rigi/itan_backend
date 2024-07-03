from rest_framework import routers
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include

from .views import views


urlpatterns = [
    path('profiles/', views.ProfilesAPIView.as_view()),
    path('profiles/addresses/', views.AddressesAPIView.as_view()),
    path('bid-files/', views.BidFilesAPIView.as_view()),
    path('business-checking-accounts/',
         views.BusinessCheckingAccountAPIView.as_view()),
    path('business-checking-accounts/<int:pk>/',
         views.BusinessCheckingAccountAPIView.as_view()),
    path('credit-cards/', views.CreditCardAPIView.as_view()),
    path('credit-cards/<int:pk>/', views.CreditCardAPIView.as_view()),
    path('documents/', views.DocumentAPIView.as_view()),
    path('documents/<int:pk>/', views.DocumentAPIView.as_view()),
    path('invoices/', views.InvoicesAPIView.as_view()),
    path('invoices/<int:pk>/', views.InvoicesAPIView.as_view()),
    path('projects/', views.ProjectsAPIView.as_view()),
    path('projects/<int:project_id>/', views.ProjectsAPIView.as_view()),
    path('projects/hide/<int:project_id>/', views.hide_project),
    path('session/', views.SessionAPIView.as_view()),
    path('users/', views.UsersAPIView.as_view()),

    path('equipments/', include('mysite.equipments.api.urls')),
]

urlpatterns = format_suffix_patterns(urlpatterns)

from rest_framework import routers
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import views


urlpatterns = [
    path('projects/', views.ProjectsAPIView.as_view()),
    path('session/', views.SessionAPIView.as_view()),
    path('users/', views.UsersAPIView.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)

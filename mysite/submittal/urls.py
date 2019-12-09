from django.urls import path
from . import views


urlpatterns = [
    path('submittal/', views.CompanySubmittalList.as_view(), name='submittalHome'),
    path('submittal/add/', views.submittal_add, name='submittalAdd'),
    path('submittal/delete/<int:submittal_id>/', views.submittal_delete, name='submittalDelete'),
    path('submittal/view/<int:submittal_id>/', views.submittal_view, name='submittalView'),
]

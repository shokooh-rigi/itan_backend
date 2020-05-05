from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path('submittal/', login_required(views.submittal_list), name='submittalHome'),
    path('submittal/add/', views.submittal_add, name='submittalAdd'),
    path('submittal/pages/<int:submittal_id>/', views.submittal_pages_ordering, name='submittalPages'),
    path('submittal/pages/delete/<int:submittal_id>/<int:submittal_form_id>/', views.submittal_form_delete,
         name='submittalFormDelete'),
    path('submittal/delete/<int:submittal_id>/', views.submittal_delete, name='submittalDelete'),
    path('submittal/view/<int:submittal_id>/', views.submittal_view, name='submittalView'),
]

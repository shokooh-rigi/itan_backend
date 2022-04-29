from django.urls import path
from . import views

urlpatterns = [
    path('', views.ts_setup_list, name='tsSetupHome'),
    path('add/<int:order_id>', views.ts_setup_edit, name='tsSetupEdit'),
]

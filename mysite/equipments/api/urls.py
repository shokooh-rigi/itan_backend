from django.urls import path
from .views import (
    create_equipment, retrieve_equipment, update_equipment, delete_equipment,
    create_data_sheet, retrieve_data_sheet, update_data_sheet, delete_data_sheet,
    clear_data_sheet, update_data_sheet_form, create_report
)

urlpatterns = [
    # Equipments
    path('equipments/', create_equipment, name='create-equipment'),
    path('equipments/<int:pk>/', retrieve_equipment, name='retrieve-equipment'),
    path('equipments/<int:pk>/update/', update_equipment, name='update-equipment'),
    path('equipments/<int:pk>/delete/', delete_equipment, name='delete-equipment'),
    # DataSheets
    path('data-sheets/', create_data_sheet, name='create-data-sheet'),
    path('data-sheets/<int:pk>/', retrieve_data_sheet, name='retrieve-data-sheet'),
    path('data-sheets/<int:pk>/update/', update_data_sheet, name='update-data-sheet'),
    path('data-sheets/<int:pk>/update/form/', update_data_sheet_form, name='update-data-sheet-form'),
    path('data-sheets/<int:pk>/delete/', delete_data_sheet, name='delete-data-sheets'),
    path('data-sheets/order/<int:pk>/delete/', clear_data_sheet, name='clear-data-sheets'),
    # Reports
    path('reports/<int:order_id>', create_report, name='create-report'),
]

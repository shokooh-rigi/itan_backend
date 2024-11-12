from django.urls import path

from .views import EstimateListView, EstimateCreateView, EstimateUpdateView, EstimateDeleteView, EstimateArchiveView, \
    EstimateDuplicateView, EstimateEquipmentView, EstimateDetailsView, EstimateBidView, EstimateHistoryView, \
    EstimateEquipmentDeleteView

urlpatterns = [
    path('estimate/get/', EstimateListView.as_view(), name='estimate-list'),
    path('estimate/create/', EstimateCreateView.as_view(), name='estimate-create'),
    path('estimate/update/<int:id>/', EstimateUpdateView.as_view(), name='estimate-update'),
    path('estimate/delete/<int:id>/', EstimateDeleteView.as_view(), name='estimate-delete'),
    path('estimate/archive/<int:id>/', EstimateArchiveView.as_view(), name='estimate-archive'),
    path('estimate/duplicate/<int:id>/', EstimateDuplicateView.as_view(), name='estimate-duplicate'),
    path('estimate/details/<int:estimate_id>/', EstimateDetailsView.as_view(), name='estimate-details'),
    path('estimate/bid/<int:estimate_id>/', EstimateBidView.as_view(), name='estimate-bid'),
    path('estimate/history/<int:estimate_id>/', EstimateHistoryView.as_view(), name='estimate-history'),
    path('estimate/equipment/<int:estimate_id>/<int:estimate_service_id>/', EstimateEquipmentView.as_view(),
         name='estimate-equipment'),
    path('estimate/equipment/delete/<int:estimate_equipment_id>/<int:interval_id>/',
         EstimateEquipmentDeleteView.as_view(), name='estimate-equipment-delete'),
]

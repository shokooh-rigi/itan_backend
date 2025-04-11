from django.urls import path

from .views import (
    EstimateListView,
    EstimateCreateView,
    EstimateUpdateView,
    EstimateDeleteView,
    EstimateArchiveView,
    EstimateDuplicateView,
    EstimateEquipmentView,
    EstimateDetailsView,
    EstimateBidView,
    EstimateHistoryView,
    EstimateEquipmentDeleteView,
    EstimateBidListView,
)

urlpatterns = [
    path("get/", EstimateListView.as_view(), name="estimate-list"),
    path("create/", EstimateCreateView.as_view(), name="estimate-create"),
    path("update/<int:id>/", EstimateUpdateView.as_view(), name="estimate-update"),
    path("delete/<int:id>/", EstimateDeleteView.as_view(), name="estimate-delete"),
    path("archive/<int:id>/", EstimateArchiveView.as_view(), name="estimate-archive"),
    path(
        "duplicate/<int:id>/",
        EstimateDuplicateView.as_view(),
        name="estimate-duplicate",
    ),
    path("details/<int:id>/", EstimateDetailsView.as_view(), name="estimate-details"),
    path(
        "bid/",
        EstimateBidListView.as_view(),
        name="estimate-bid",
    ),
    path(
        "bid/<int:bid_id>/",
        EstimateBidListView.as_view(),
        name="estimate-bid-list",
    ),
    path(
        "history/<int:estimate_id>/",
        EstimateHistoryView.as_view(),
        name="estimate-history",
    ),
    path(
        "equipment/<int:estimate_id>/<int:service_id>/",
        EstimateEquipmentView.as_view(),
        name="estimate-equipment",
    ),
    path(
        "equipment/delete/<int:estimate_equipment_id>/<int:interval_id>/",
        EstimateEquipmentDeleteView.as_view(),
        name="estimate-equipment-delete",
    ),
]

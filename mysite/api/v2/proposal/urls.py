from django.urls import path

from .views import (
    ProposalEstimateListView,
    ProposalCreateView,
    ProposalArchiveView,
    ProposalDeleteView,
    ProposalListView,
    ProposalDetailView,
)

urlpatterns = [
    path("list/", ProposalListView.as_view(), name="proposal-list"),
    path("create/", ProposalCreateView.as_view(), name="proposal-create"),
    path(
        "archive/<int:id>/",
        ProposalArchiveView.as_view(),
        name="proposal-archive",
    ),
    path(
        "delete/<int:id>/",
        ProposalDeleteView.as_view(),
        name="proposal-delete",
    ),
    path(
        "estimate/<int:estimate_id>/",
        ProposalEstimateListView.as_view(),
        name="proposal-estimate",
    ),
    path(
        "estimate/",
        ProposalEstimateListView.as_view(),
        name="proposal-estimate",
    ),
    path(
        "list/<int:id>/",
        ProposalDetailView.as_view(),
        name="proposal-list_by_id",
    ),
]

from django.urls import path

from .views import (
    BidListView,
    BidDetailListView,
    BidUpdateView,
    BidDuplicateView,
    BidArchiveView,
    BidDeleteView,
    BidCreateView,
    BidAddFileView,
    BidListView,
    BidAttachmentRetrieveUpdateDestroyView,
    BidAttachmentRetrieveView,
    BidAttachmentListCreateView,
)


urlpatterns = [
    path("get/", BidListView.as_view(), name="bid-lists"),
    path("get/<int:id>/", BidDetailListView.as_view(), name="bid-list_by_id"),
    path("create/", BidCreateView.as_view(), name="bid-create"),
    path("add/file/<int:id>/", BidAddFileView.as_view(), name="bid-add-file"),
    path("update/<int:bid_id>/", BidUpdateView.as_view(), name="bid-update"),
    path("duplicate/<int:bid_id>/", BidDuplicateView.as_view(), name="bid-duplicate"),
    path("archive/<int:bid_id>/", BidArchiveView.as_view(), name="bid-archive"),
    path("delete/<int:bid_id>/", BidDeleteView.as_view(), name="bid-delete"),
    path(
        "<int:bid_id>/attachments/",
        BidAttachmentListCreateView.as_view(),
        name="bid-attachment-list-create",
    ),
    path(
        "attachments/<int:pk>/",
        BidAttachmentRetrieveView.as_view(),
        name="bid-attachment-retrieve",
    ),
    path(
        "attachments/<int:pk>/update/",
        BidAttachmentRetrieveUpdateDestroyView.as_view(),
        name="bid-attachment-update-delete",
    ),
]

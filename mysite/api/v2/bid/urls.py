from django.urls import path

from .views import (
    BidListView,
    BidUpdateView,
    BidDuplicateView,
    BidArchiveView,
    BidDeleteView,
    BidCreateView,
    BidAddFileView,
    BidListView,
)


urlpatterns = [
    path('bid/get/', BidListView.as_view(), name='bid-lists'),
    path('bid/get/<int:id>/', BidListView.as_view(), name='bid-list_by_id'),
    path('bid/create/', BidCreateView.as_view(), name='bid-create'),
    path('bid/add/file/<int:id>/', BidAddFileView.as_view(), name='bid-add-file'),
    path('bid/update/<int:bid_id>/', BidUpdateView.as_view(), name='bid-update'),
    path('bid/duplicate/<int:bid_id>/', BidDuplicateView.as_view(), name='bid-duplicate'),
    path('bid/archive/<int:bid_id>/', BidArchiveView.as_view(), name='bid-archive'),
    path('bid/delete/<int:bid_id>/', BidDeleteView.as_view(), name='bid-delete'),
]

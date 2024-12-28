from django.urls import path

from .views import (
    BidFileListView,
    BidFileUpdateView,
    BidFileDuplicateView,
    BidFileArchiveView,
    BidFileDeleteView,
    BidFileCreateView,
    BidFileAddFileView,
)


urlpatterns = [
    path('bid/get/', BidFileListView.as_view(), name='bid-list'),
    path('bid/create/', BidFileCreateView.as_view(), name='bid-create'),
    path('bid/add/file/<int:id>/', BidFileAddFileView.as_view(), name='bid-add-file'),
    path('bid/update/<int:bid_id>/', BidFileUpdateView.as_view(), name='bid-update'),
    path('bid/duplicate/<int:bid_id>/', BidFileDuplicateView.as_view(), name='bid-duplicate'),
    path('bid/archive/<int:id>/', BidFileArchiveView.as_view(), name='bid-archive'),
    path('bid/delete/<int:bid_id>/', BidFileDeleteView.as_view(), name='bid-delete'),
]

from django.urls import path

from .views import (
    BidFileListView,
    BidFileUpdateView,
    BidFileDuplicateView,
    BidFileArchiveView,
    BidFileDeleteView,
    BidFileCreateView,
    BidFileAddFileView, 
    BidListView,
)


urlpatterns = [
    path('bid/create/', BidFileCreateView.as_view(), name='bid-create'),
    path('bid/get/', BidFileListView.as_view(), name='bid-lists'),
    path('bid/get/<int:id>/', BidListView.as_view(), name='bid-list_by_id'),
    path('bid/update/<int:bid_id>/', BidFileUpdateView.as_view(), name='bid-update'),
    path('bid/duplicate/<int:bid_id>/', BidFileDuplicateView.as_view(), name='bid-duplicate'),
    path('bid/archive/<int:bid_id>/', BidFileArchiveView.as_view(), name='bid-archive'),
    path('bid/delete/<int:bid_id>/', BidFileDeleteView.as_view(), name='bid-delete'),
    path('bid/files/<int:id>/', BidFileAddFileView.as_view(), name='bid-add-file'),
]

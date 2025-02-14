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
    BidAttachmentRetrieveUpdateDestroyView,
    BidAttachmentRetrieveView,
    BidAttachmentListCreateView,
)


urlpatterns = [
    path('bid/get/', BidFileListView.as_view(), name='bid-lists'),
    path('bid/get/<int:id>/', BidListView.as_view(), name='bid-list_by_id'),
    path('bid/create/', BidFileCreateView.as_view(), name='bid-create'),
    path('bid/add/file/<int:id>/', BidFileAddFileView.as_view(), name='bid-add-file'),
    path('bid/update/<int:bid_id>/', BidFileUpdateView.as_view(), name='bid-update'),
    path('bid/duplicate/<int:bid_id>/', BidFileDuplicateView.as_view(), name='bid-duplicate'),
    path('bid/archive/<int:bid_id>/', BidFileArchiveView.as_view(), name='bid-archive'),
    path('bid/delete/<int:bid_id>/', BidFileDeleteView.as_view(), name='bid-delete'),
    path('bid/attachments/', BidAttachmentListCreateView.as_view(), name='bid-attachment-list-create'),
    path('bid/attachments/<int:pk>/', BidAttachmentRetrieveView.as_view(), name='bid-attachment-retrieve'),
    path('bid/attachments/<int:pk>/update/', BidAttachmentRetrieveUpdateDestroyView.as_view(),
         name='bid-attachment-update-delete'),
]
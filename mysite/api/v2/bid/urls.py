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
    path('bidfiles/get/', BidFileListView.as_view(), name='bidfile-list'),
    path('bidfiles/create/', BidFileCreateView.as_view(), name='bidfile-create'),
    path('bidfile/add/file/<int:id>/', BidFileAddFileView.as_view(), name='bidfile-add-file'),
    path('bidfiles/update/<int:bidfiles_id>/', BidFileUpdateView.as_view(), name='bidfile-update'),
    path('bidfiles/duplicate/<int:bidfiles_id>/', BidFileDuplicateView.as_view(), name='bidfile-duplicate'),
    path('bidfiles/archive/<int:id>/', BidFileArchiveView.as_view(), name='bidfile-archive'),
    path('bidfiles/delete/<int:bidfiles_id>/', BidFileDeleteView.as_view(), name='bidfile-delete'),
]

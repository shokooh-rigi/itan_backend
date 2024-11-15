from django.urls import path

from .views import (
    BidFileListView,
    BidFileUpdateView,
    BidFileDuplicateView,
    BidFileArchiveView,
    BidFileDeleteView,
    BidCreateView,
    BidCreateFileView,
)


urlpatterns = [
    path('bidfiles/get/', BidFileListView.as_view(), name='bidfile-list'),
    path('bid/create/', BidCreateView.as_view(), name='bid-create'),
    path('bid/create/file/<int: id>/', BidCreateFileView.as_view(), name='bid-create-file'),
    path('bidfiles/update/<int:bidfiles_id>/', BidFileUpdateView.as_view(), name='bidfile-update'),
    path('bidfiles/duplicate/<int:bidfiles_id>/', BidFileDuplicateView.as_view(), name='bidfile-duplicate'),
    path('bidfiles/archive/<int:id>/', BidFileArchiveView.as_view(), name='bidfile-archive'),
    path('bidfiles/delete/<int:bidfiles_id>/', BidFileDeleteView.as_view(), name='bidfile-delete'),
]

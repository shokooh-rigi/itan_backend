from django.urls import path
from .views import BidFileListView, BidFileCreateView, BidFileUpdateView, BidFileDeleteView

urlpatterns = [
    path('bid/get', BidFileListView.as_view(), name='ibidFilesList'),
    path('bid/create/', BidFileCreateView.as_view(), name='ibidFilesCreate'),
    path('bid/update/<int:bid_files_id>/', BidFileUpdateView.as_view(), name='ibidFilesUpdate'),
    path('bid/delete/<int:bid_files_id>/', BidFileDeleteView.as_view(), name='ibidFilesDelete'),
]

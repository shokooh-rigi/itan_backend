from django.urls import path
from .views import BidFileListView, BidFileCreateView, BidFileUpdateView, BidFileDeleteView

urlpatterns = [
    path('ibid/get/', BidFileListView.as_view(), name='ibidFilesList'),
    path('ibid/create/', BidFileCreateView.as_view(), name='ibidFilesCreate'),
    path('ibid/update/<int:id>/', BidFileUpdateView.as_view(), name='ibidFilesUpdate'),
    path('ibid/delete/<int:id>/', BidFileDeleteView.as_view(), name='ibidFilesDelete'),
]

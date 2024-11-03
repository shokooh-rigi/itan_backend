from django.urls import path
from .views import BidFileArchiveView

urlpatterns = [
    path('bid/archive/<int:id>/', BidFileArchiveView.as_view(), name='ibidFilesArchive'),
]

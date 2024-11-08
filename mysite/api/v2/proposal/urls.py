from django.urls import path

from .views import ProposalListView, ProposalCreateView, ProposalArchiveView, ProposalDeleteView

urlpatterns = [
    path('proposal/get/', ProposalListView.as_view(), name='proposal-list'),
    path('proposal/create/', ProposalCreateView.as_view(), name='proposal-create'),
    path('proposal/archive/<int:id>/', ProposalArchiveView.as_view(), name='proposal-archive'),
    path('proposal/delete/<int:id>/', ProposalDeleteView.as_view(), name='proposal-delete'),
]

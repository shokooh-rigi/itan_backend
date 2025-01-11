from django.urls import path

from .views import ProposalEstimateListView, ProposalCreateView, ProposalArchiveView, ProposalDeleteView, \
    ProposalListView

urlpatterns = [
    path('proposal/get/', ProposalListView.as_view(), name='proposal-list'),
    path('proposal/create/', ProposalCreateView.as_view(), name='proposal-create'),
    path('proposal/archive/<int:id>/', ProposalArchiveView.as_view(), name='proposal-archive'),
    path('proposal/delete/<int:id>/', ProposalDeleteView.as_view(), name='proposal-delete'),
    path('proposal/estimate/', ProposalEstimateListView.as_view(), name='proposal-estimate'),

]

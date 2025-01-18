from django.urls import path

from mysite.api.v2.coi.views import CoiListView, CoiCreateView

urlpatterns = [
    path('cois/', CoiListView.as_view(), name='coi-list'),
    path('cois/create/', CoiCreateView.as_view(), name='coi-create'),
]

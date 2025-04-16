from django.urls import path

from mysite.api.v2.coi.views import CoiListView, CoiCreateView, CoiUpdateView, CoiDeleteView

urlpatterns = [
    path(
        'cois/',
        CoiListView.as_view(),
        name='coi-list'
    ),
    path(
        'cois/create/',
        CoiCreateView.as_view(),
        name='coi-create'
    ),
    path(
        'cois/<int:pk>/update/',
        CoiUpdateView.as_view(),
        name='coi-update'
    ),
    path(
        'cois/<int:pk>/delete/',
        CoiDeleteView.as_view(),
        name='coi-delete'
    ),
]

from django.urls import path
from .views import ProjectProcessListView, ProjectProcessView

urlpatterns = [
    path(
        'project-processes/list/',
        ProjectProcessListView.as_view(),
        name='project-process-list'
    ),
    path(
        'project-processes/<int:order_id>/<int:pre_demo>/',
        ProjectProcessView.as_view(),
        name='project-process'
    ),
]

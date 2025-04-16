from django.urls import path

from .views import (
    ScheduleListView,
    ScheduleUpdateView,
    ScheduleArchiveView,
    ScheduleDeleteView,
    ScheduleCreateView,
)


urlpatterns = [
    path(
        'schedule/get/',
        ScheduleListView.as_view(),
        name='schedule-list'
    ),
    path(
        'schedule/create/',
        ScheduleCreateView.as_view(),
        name='schedule-create'
    ),
    path(
        'schedule/update/<int:schedule_id>/',
        ScheduleUpdateView.as_view(),
        name='schedule-update'
    ),
    path(
        'schedule/archive/<int:id>/',
        ScheduleArchiveView.as_view(),
        name='schedule-archive'
    ),
    path(
        'schedule/delete/<int:schedule_id>/',
        ScheduleDeleteView.as_view(),
        name='schedule-delete'
    ),
]

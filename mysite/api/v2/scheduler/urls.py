from django.urls import path

from .views import (
    ScheduleListView,
    ScheduleTechCreateView,
    ScheduleUpdateView,
    ScheduleArchiveView,
    ScheduleDeleteView,
    ScheduleCreateView,
    ScheduleTechListView,
    ScheduleTechDetailView,
    ScheduleTechUpdateView,
    ScheduleTechDeleteView,
)

urlpatterns = [
    path("schedule/get/", ScheduleListView.as_view(), name="schedule-list"),
    path("schedule/create/", ScheduleCreateView.as_view(), name="schedule-create"),
    path(
        "schedule/update/<int:schedule_id>/",
        ScheduleUpdateView.as_view(),
        name="schedule-update",
    ),
    path(
        "schedule/archive/<int:id>/",
        ScheduleArchiveView.as_view(),
        name="schedule-archive",
    ),
    path(
        "schedule/delete/<int:schedule_id>/",
        ScheduleDeleteView.as_view(),
        name="schedule-delete",
    ),
    path("schedule/techs/", ScheduleTechListView.as_view(), name="schedule-tech-list"),
    path(
        "schedule/tech/<int:schedule_id>/",
        ScheduleTechDetailView.as_view(),
        name="schedule-tech-detail",
    ),
    path(
        "schedule/tech/create/<int:schedule_id>/<int:tech_id>/",
        ScheduleTechCreateView.as_view(),
        name="schedule-tech-update",
    ),
    path(
        "schedule/tech/update/<int:schedule_id>/<int:tech_id>/",
        ScheduleTechUpdateView.as_view(),
        name="schedule-tech-update",
    ),
    path(
        "schedule/tech/delete/<int:schedule_id>/<int:tech_id>/",
        ScheduleTechDeleteView.as_view(),
        name="schedule-tech-delete",
    ),
]

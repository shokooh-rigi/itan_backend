from django.urls import path

from .views import *

urlpatterns = [
    path('schedule/', schedule_list, name='scheduleHome'),
    path('schedule/add/', schedule_add, name='scheduleAdd'),
    path('schedule/edit/<int:schedule_id>/', schedule_edit, name='scheduleEdit'),
    path('schedule/archive/<int:schedule_id>/', schedule_archive, name='scheduleArchive'),
    path('schedule/delete/<int:schedule_id>/', schedule_delete, name='scheduleDelete'),
    path('schedule/add_test/', schedule_add_test, name='scheduleAdd_test'),
]

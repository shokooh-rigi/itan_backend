from django.urls import path

from .views import *

urlpatterns = [
    path('schedule/', schedule_list, name='scheduleHome'),
    path('schedule/add/', schedule_add, name='scheduleAdd'),
    path('schedule/edit/<int:schedule_id>/', schedule_edit, name='scheduleEdit'),
    path('schedule/archive/<int:schedule_id>/', schedule_archive, name='scheduleArchive'),
    path('schedule/delete/<int:schedule_id>/', schedule_delete, name='scheduleDelete'),
    path('schedule/calendar/', schedule_calendar, name='scheduleCalendar'),
    path('schedule/get_schedule_list/<int:type>/', schedule_orders_list, name='get_schedule_list'),
    path('schedule/get_tech_list/', schedule_tech_list, name='get_tech_list'),
    path('schedule/create_schedule/', create_schedule, name='create_schedule'),
    path('schedule/update_schedule/', update_schedule, name='update_schedule'),
]

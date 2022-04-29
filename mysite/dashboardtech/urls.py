from django.urls import path

from .views import *

app_name = 'techPanel'
urlpatterns = [
    path('schedule/', tech_calendar, name='schedule'),
    path('get_schedule_list/', schedule_list, name='get_schedule_list'),
    path('update_note/', update_note, name='update_note'),
    path('upload_tech/', upload_tech, name='upload_tech'),
]

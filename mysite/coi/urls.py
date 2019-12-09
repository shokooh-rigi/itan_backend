from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from mysite.coi import views as coi_views

urlpatterns = [
    path('coi/', coi_views.coi_list, name='CoiHome'),
    path('coi/new/', coi_views.coi_create, name='CoiCreate'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

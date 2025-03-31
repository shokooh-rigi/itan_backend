from django.urls import path

from mysite.api.v2.coi.views import PerformanceListView

urlpatterns = [
    path('report/performance', PerformanceListView.as_view(), name='performance'),
]

from django.urls import path

from mysite.api.v2.report.views import PerformanceListView, JobCostingListView

urlpatterns = [
    path('report/performance', PerformanceListView.as_view(), name='performance'),
    path('report/jobcosting', JobCostingListView.as_view(), name='job-costing'),
]

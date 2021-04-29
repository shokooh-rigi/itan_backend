from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from mysite.estimator.models import *
from mysite.estimator.views import estimate_total_calculator
from mysite.order.models import Order
from ..settings import MEDIA_URL, WEB_URL
from ..scheduler.models import Schedule, Maintenance


@login_required
def job_costing_list(request):
    object_list = Order.objects.filter(invoice__isnull=False).order_by('created_on')

    parameters = {
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
        'object_list': object_list,
    }
    return render(request, "jobCostsList.html", parameters)


def estimat_total_work(estimate_id):
    estimate_equipments = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
    estimate_work = 0
    for each_estimate_equipment in estimate_equipments:
        work_total = int(each_estimate_equipment.quantity) * int(each_estimate_equipment.equipment.estimate_work)
        estimate_work += int(work_total)
    estimate_work = estimate_work/60
    return estimate_work


def actual_total_work(order_id):
    schedules = Schedule.objects.filter(order_id=order_id)
    maintenances = Maintenance.objects.filter(order__id=order_id)
    actual_work = 0
    for schedule in schedules:
        work_total = schedule.schedule_end - schedule.schedule_start
        actual_work += int(work_total.total_seconds())
    for maintenance in maintenances:
        work_total = maintenance.schedule_end - maintenance.schedule_start
        actual_work += int(work_total.total_seconds())
    actual_work = actual_work/3600
    return actual_work

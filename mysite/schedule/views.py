import datetime

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from mysite.order.models import Order
from .forms import ScheduleForm
from .models import Schedule
from ..settings import MEDIA_URL, WEB_URL


# Create your views here.


@login_required
def schedule_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    from_date = request.GET.get("fromDate", '01/01/2000')
    to_date = request.GET.get("toDate", '01/01/2100')
    if from_date and to_date:
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y')
        to_date_obj = to_date_obj + datetime.timedelta(hours=23, minutes=59, seconds=59)

        object_list = Schedule.objects.filter(Q(order__project_number__icontains=search)
                                              | Q(assigned_to_contractor__name__icontains=search)
                                              | Q(assigned_to_contractor__company__name__icontains=search)) \
            .filter(scheduled_for__range=(from_date_obj, to_date_obj)).order_by(ordering)

    else:
        object_list = Schedule.objects.filter(Q(order__project_number__icontains=search)
                                              | Q(assigned_to_contractor__name__icontains=search)
                                              | Q(assigned_to_contractor__company__name__icontains=search)) \
            .order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    schedules = paginator.get_page(page)

    parameters = {'schedules': schedules,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "schedule.html", parameters)


@login_required
def schedule_add(request):
    form = ScheduleForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    orders = Order.objects.filter(archive=False).exclude(id__in=Schedule.objects.all().values_list('order_id')) \
        .order_by('-created_on')
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('scheduleHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                form.save()
                return redirect('scheduleHome')
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "scheduleAdd.html", parameters)


@login_required
def schedule_edit(request, schedule_id):
    this_schedule = get_object_or_404(Schedule, id=schedule_id)
    form = ScheduleForm(request.POST or None, request.FILES or None, instance=this_schedule)
    orders = Order.objects.filter(archive=False).exclude(id__in=Schedule.objects.all().values_list('order_id')) \
        .order_by('-created_on')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('scheduleHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('scheduleHome')
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "scheduleEdit.html", parameters)


@login_required
def schedule_archive(request, schedule_id):
    this_schedule = get_object_or_404(Schedule, id=schedule_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_schedule.archive = True
            this_schedule.save()
        return redirect('scheduleHome')
    parameters = {'this_schedule': this_schedule
                  }
    return render(request, "scheduleArchive.html", parameters)


@login_required
def schedule_delete(request, schedule_id):
    this_schedule = get_object_or_404(Schedule, id=schedule_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_schedule.delete()
        return redirect('scheduleHome')
    parameters = {'this_schedule': this_schedule
                  }
    return render(request, "ScheduleDelete.html", parameters)

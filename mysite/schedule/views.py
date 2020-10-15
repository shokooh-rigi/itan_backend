import datetime
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django import forms
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
import random
from mysite.order.models import Order
from .forms import ScheduleForm
from .models import Schedule, User, Profile
from ..settings import MEDIA_URL, WEB_URL, TIME_ZONE
from datetime import timedelta
from django.utils.timezone import activate
import mysite.settings
from ..estimator.views import estimate_total_work

# activate(TIME_ZONE)

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
            .filter(schedule_start__range=(from_date_obj, to_date_obj)).order_by(ordering)

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


@login_required
def schedule_calendar(request):
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('scheduleHome')
        elif request.POST.get("next"):
            return redirect('scheduleHome')
    parameters = {}
    return render(request, "schedule_calendar.html", parameters)


@login_required
def schedule_orders_list(request, type):
    if type == 1:
        scheduled = Schedule.objects.all()
        response_data = []
        for schedule in scheduled:

            full_address = ''
            if schedule.order.proposal.quote.estimate.project.address_line_1:
                full_address += schedule.order.proposal.quote.estimate.project.address_line_1
            if schedule.order.proposal.quote.estimate.project.address_line_2:
                full_address += ' ' + schedule.order.proposal.quote.estimate.project.address_line_2
            if schedule.order.proposal.quote.estimate.project.city:
                full_address += ' ' + schedule.order.proposal.quote.estimate.project.city
            if schedule.order.proposal.quote.estimate.project.state:
                full_address += ' ' + schedule.order.proposal.quote.estimate.project.state
            if schedule.order.proposal.quote.estimate.project.zip:
                full_address += ' ' + schedule.order.proposal.quote.estimate.project.zip

            if schedule.assigned_to_employee:
                calendar_id = schedule.assigned_to_employee.id
            else:
                calendar_id = 0
            response_data.append({
                'id': str(schedule.order.id),
                'calendarId': str(calendar_id),
                'title': schedule.order.project_number + ': ' + str(schedule.order.proposal.quote.estimate.project),
                'location': full_address,
                'category': 'time',
                'start': schedule.schedule_start,
                'end': schedule.schedule_end,
                'goingDuration': str(30),
                'comingDuration': str(30),
            })

        return JsonResponse(response_data, safe=False)
    elif type == 2:
        orders = Order.objects.filter(schedule__isnull=True)
        response_data = []
        for order in orders:
            full_address = ''
            if order.proposal.quote.estimate.project.address_line_1:
                full_address += order.proposal.quote.estimate.project.address_line_1
            if order.proposal.quote.estimate.project.address_line_2:
                full_address += ' ' + order.proposal.quote.estimate.project.address_line_2
            if order.proposal.quote.estimate.project.city:
                full_address += ' ' + order.proposal.quote.estimate.project.city
            if order.proposal.quote.estimate.project.state:
                full_address += ' ' + order.proposal.quote.estimate.project.state
            if order.proposal.quote.estimate.project.zip:
                full_address += ' ' + order.proposal.quote.estimate.project.zip
            response_data.append({
                'id': order.id,
                'number': order.project_number,
                'title': order.project_number,
                'body': order.project_number + ': ' + str(order.proposal.quote.estimate.project),
                'location': full_address,
                'category': 'time',
                'estimated_work': estimate_total_work(order.proposal.quote.estimate.id)
            })

        return JsonResponse(response_data, safe=False)


@login_required
def schedule_tech_list(request):
    tech_list = User.objects.filter(Q(profile__user_type=5) | Q(profile__user_type=6))
    r = lambda: random.randint(0, 230)
    response_data = []
    response_data.append({
        'id': '0',
        'calendar_id': '0',
        'calendar_name': 'Not Assigned',
        'calendar_color': '#ffffff',
        'calendar_bg_color': '#000000'
    })
    for tech in tech_list:
        random_color = '#%02X%02X%02X' % (r(),r(),r())
        response_data.append({
            'id': tech.id,
            'calendar_id': tech.id,
            'calendar_name': tech.first_name + " " + tech.last_name,
            'calendar_color': '#ffffff',
            'calendar_bg_color': random_color
        })

    return JsonResponse(response_data, safe=False)


@login_required
def create_schedule(request):
    if request.method == "POST" and request.is_ajax():
        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id)
        schedule_date_start = request.POST.get('schedule_start')
        schedule_date_end = request.POST.get('schedule_end')
        current_user = request.user
        new_schedule = Schedule(order=order, schedule_start=schedule_date_start, schedule_end=schedule_date_end, created_by=current_user)
        new_schedule.save()
        return JsonResponse('New Schedule created on database successfully.', safe=False)
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


@login_required
def update_schedule(request):
    if request.method == "POST" and request.is_ajax():
        update_type = request.POST.get('type')
        order_id = request.POST.get('org_order_id')
        schedule_update = Schedule.objects.get(order__id=order_id)
        new_tech_id = request.POST.get('new_tech_id')
        if update_type == 'calendar_delete':
            schedule_update.delete()
            return JsonResponse('Schedule Deleted from database successfully.', safe=False)
        else:
            if new_tech_id == '0':
                schedule_update.assigned_to_employee = None
            else:
                schedule_update.assigned_to_employee = User.objects.get(id=new_tech_id)
                this_tech_schedules = Schedule.objects.filter(Q(assigned_to_employee__id=new_tech_id,
                                                              schedule_start__lt=schedule_update.schedule_start,
                                                              schedule_end__gt=schedule_update.schedule_start) |
                                                              Q(assigned_to_employee__id=new_tech_id,
                                                              schedule_start__gt=schedule_update.schedule_start,
                                                              schedule_start__lt=schedule_update.schedule_end))
                if this_tech_schedules:
                    return JsonResponse('busy', safe=False)
            if update_type == 'tech_update':
                schedule_update.save()
            elif update_type == 'calendar_update':
                new_date = request.POST.get('new_date')
                new_date_end = request.POST.get('new_date_end')
                start_check = parse_datetime(new_date) - timedelta(minutes=30)
                end_check = parse_datetime(new_date_end) + timedelta(minutes=30)
                this_tech_schedules = Schedule.objects.filter(Q(assigned_to_employee__id=new_tech_id,
                                                              schedule_start__lt=start_check,
                                                              schedule_end__gt=start_check) |
                                                              Q(assigned_to_employee__id=new_tech_id,
                                                              schedule_start__gt=start_check,
                                                              schedule_start__lt=end_check)).exclude(order__id=order_id)
                if this_tech_schedules:
                    return JsonResponse('busy', safe=False)
                schedule_update.schedule_start = new_date
                schedule_update.schedule_end = new_date_end
                schedule_update.save()
            return JsonResponse('Schedule updated on database successfully.', safe=False)
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)

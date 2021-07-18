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
from .models import *
from ..settings import MEDIA_URL, WEB_URL, TIME_ZONE
from datetime import timedelta
from django.utils.timezone import activate
import mysite.settings
from ..estimator.views import estimate_total_work
from ..core.models import *
import json
from ..projectprocess.models import ProjectProcess, ProjectProcessPreDemo


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
    form = ScheduleForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('scheduleHome')
        elif request.POST.get("next"):
            return redirect('scheduleHome')
    orders_list = Order.objects.filter(archive=False)
    parameters = {
        'form': form,
        'orders_list': orders_list
    }
    return render(request, "schedule_calendar.html", parameters)


@login_required
def schedule_orders_list(request, type):
    if type == 1:
        maintenace_list = Maintenance.objects.all()
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

            # if schedule.assigned_to_employee:
            #     calendar_id = schedule.assigned_to_employee.id
            # else:
            #     calendar_id = 0
            assigned_to_employees = []
            assigned_to_employees_names = []
            assigned_to_contractors = []
            assigned_to_contractors_names = []
            for schedule_tech in ScheduleTech.objects.filter(schedule=schedule).all():
                if schedule_tech.assigned_to_employee:
                    assigned_to_employees.append(schedule_tech.assigned_to_employee.id)
                    if schedule_tech.assigned_to_employee.last_name:
                        assigned_to_employees_names.append(
                            schedule_tech.assigned_to_employee.first_name + ' ' + schedule_tech.assigned_to_employee.last_name)
                    else:
                        assigned_to_employees_names.append(schedule_tech.assigned_to_employee.email)
                elif schedule_tech.assigned_to_contractor:
                    assigned_to_contractors.append(schedule_tech.assigned_to_contractor.id)
                    if schedule_tech.assigned_to_contractor.last_name:
                        assigned_to_contractors_names.append(
                            schedule_tech.assigned_to_contractor.first_name + ' ' + schedule_tech.assigned_to_contractor.last_name)
                    else:
                        assigned_to_contractors_names.append(schedule_tech.assigned_to_contractor.email)
            any_assigned = False
            if ScheduleTech.objects.filter(schedule=schedule).count() > 0:
                any_assigned = True
            poc_name = ''
            poc_cell_phone = ''
            poc_office_phone = ''
            tech_notes = ''
            try:
                poc_name = schedule.order.techlabel.point_of_contact_name
                tech_notes = schedule.order.techlabel.tech_notes
                if schedule.order.techlabel.point_of_contact_cell_phone:
                    poc_cell_phone = schedule.order.techlabel.point_of_contact_cell_phone
                if schedule.order.techlabel.point_of_contact_office_phone:
                    poc_office_phone = schedule.order.techlabel.point_of_contact_office_phone
            except:
                pass
            response_data.append({
                'order_id': str(schedule.order.id),
                'schedule_id': str(schedule.id),
                'assigned_to_employees': assigned_to_employees,
                'assigned_to_contractors': assigned_to_contractors,
                'assigned_to_employees_names': assigned_to_employees_names,
                'assigned_to_contractors_names': assigned_to_contractors_names,
                'project_number': schedule.order.project_number,
                'project_name': str(schedule.order.proposal.quote.estimate.project),
                'customer': str(schedule.order.proposal.quote.estimate.customer.company.name),
                'engineer': str(schedule.order.proposal.quote.estimate.engineer.company.name),
                'predemo': schedule.order.proposal.quote.estimate.estimatedetails.pre_demo,
                'is_predemo': schedule.pre_demo,
                'poc_name': poc_name,
                'poc_cell_phone': poc_cell_phone,
                'poc_office_phone': poc_office_phone,
                'control_system': str(schedule.order.control_system),
                'special_instruction': tech_notes,
                'title': str(schedule.order.proposal.quote.estimate.project),
                'assigned': any_assigned,
                'location': full_address,
                'category': 'time',
                'start': schedule.schedule_start,
                'end': schedule.schedule_end,
                'estimate': estimate_total_work(schedule.order.proposal.quote.estimate.id),
                'goingDuration': str(30),
                'comingDuration': str(30),
                'partial': schedule.order.partial_job_done,
            })

        for maintenance in maintenace_list:
            assigned_to_employees = []
            assigned_to_employees_names = []
            assigned_to_contractors = []
            assigned_to_contractors_names = []
            if maintenance.assigned_to_employee:
                assigned_to_employees.append(maintenance.assigned_to_employee.id)
                if maintenance.assigned_to_employee.last_name:
                    assigned_to_employees_names.append(maintenance.assigned_to_employee.first_name + ' ' + maintenance.assigned_to_employee.last_name)
                else:
                    assigned_to_employees_names.append(maintenance.assigned_to_employee.email)
            elif maintenance.assigned_to_contractor:
                assigned_to_contractors.append(maintenance.assigned_to_contractor.id)
                if maintenance.assigned_to_contractor.last_name:
                    assigned_to_contractors_names.append(
                        maintenance.assigned_to_contractor.first_name + ' ' + maintenance.assigned_to_contractor.last_name)
                else:
                    assigned_to_contractors_names.append(maintenance.assigned_to_contractor.email)
            any_assigned = False
            if maintenance.assigned_to_employee or maintenance.assigned_to_contractor:
                any_assigned = True
            details_completed = False
            if maintenance.order and any_assigned:
                details_completed = True
            maintenance_order_id = ''
            maintenance_title = 'Maintenace'
            if maintenance.order:
                maintenance_title = str(maintenance.order.project_number + '<br />' + str(maintenance.order.proposal.quote.estimate.project))
                maintenance_order_id = maintenance.order.id
            color = '#fff'
            if maintenance.maintenance_type == 1:
                if details_completed:
                    color = '#000'
                    bg_color = '#ffc107'
                else:
                    bg_color = '#6c757d'
            if maintenance.maintenance_type == 2:
                maintenance_title = 'Lost Time'
                if maintenance.order:
                    maintenance_title = str(maintenance.order.project_number + '<br />' + str(
                        maintenance.order.proposal.quote.estimate.project))
                if details_completed:
                    bg_color = '#c82333'

                else:
                    bg_color = '#6c757d'
            if maintenance.maintenance_type == 3:
                maintenance_title = 'Off/Vacation'
                if any_assigned:
                    details_completed = True
                if details_completed:
                    bg_color = '#23272b'
                else:
                    bg_color = '#6c757d'
            response_data.append({
                'order_id': maintenance_order_id,
                'maintenance_id': str(maintenance.id),
                'assigned_to_employees': assigned_to_employees,
                'assigned_to_contractors': assigned_to_contractors,
                'assigned_to_employees_names': assigned_to_employees_names,
                'assigned_to_contractors_names': assigned_to_contractors_names,
                'title': maintenance_title,
                'completed': details_completed,
                'category': 'time',
                'start': maintenance.schedule_start,
                'end': maintenance.schedule_end,
                'goingDuration': str(30),
                'comingDuration': str(30),
                'bg_color': bg_color,
                'color': color,
            })
        return JsonResponse(response_data, safe=False)
    elif type == 2:
        # orders = Order.objects.filter(projectprocess__job_completed=False).order_by('project_number')
        orders = Order.objects.all().order_by('project_number')
        response_data = []
        for order in orders:
            if ProjectProcess.objects.filter(order=order).exists():
                if not order.projectprocess.tech_scheduled:
                    color = '#3699ff'
                elif order.projectprocess.tech_scheduled and not order.projectprocess.job_completed:
                    color = '#8950fc'
                else:
                    color = '#3699ff'
            else:
                color = '#3699ff'
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
                'estimated_work': estimate_total_work(order.proposal.quote.estimate.id),
                'color': color,
                'predemo': False
            })
            if order.proposal.quote.estimate.estimatedetails.pre_demo != 0:
                if ProjectProcessPreDemo.objects.filter(order=order).exists():
                    if not order.projectprocesspredemo.tech_scheduled:
                        color = '#3699ff'
                    elif order.projectprocesspredemo.tech_scheduled and not order.projectprocesspredemo.job_completed:
                        color = '#8950fc'
                else:
                    color = '#3699ff'
                response_data.append({
                    'id': order.id,
                    'number': order.project_number,
                    'title': order.project_number,
                    'body': order.project_number + ': ' + str(order.proposal.quote.estimate.project) + ' - PREDEMO',
                    'location': full_address,
                    'category': 'time',
                    'estimated_work': estimate_total_work(order.proposal.quote.estimate.id),
                    'color': color,
                    'predemo': True
                })

        return JsonResponse(response_data, safe=False)


@login_required
def schedule_tech_list(request):
    employee_list = User.objects.filter(Q(profile__user_type=5) | Q(profile__user_type=6))
    r = lambda: random.randint(0, 230)
    response_data = []
    # response_data.append({
    #     'id': '0',
    #     'type': '0',
    #     'calendar_id': '0',
    #     'calendar_name': 'Not Assigned',
    #     'calendar_color': '#ffffff',
    #     'calendar_bg_color': '#000000'
    # })
    for employee in employee_list:
        random_color = '#%02X%02X%02X' % (r(), r(), r())
        response_data.append({
            'id': employee.id,
            'type': 'employee' if employee.profile.status == 1 else 'contractor',
            'calendar_id': employee.id,
            'calendar_name': employee.first_name + " " + employee.last_name,
            'calendar_color': '#ffffff',
            'calendar_bg_color': random_color
        })
    return JsonResponse(response_data, safe=False)


@login_required
def create_schedule(request):
    if request.method == "POST" and request.is_ajax():
        if request.POST.get('maintenance'):
            current_user = request.user
            schedule_date_start = request.POST.get('schedule_start')
            schedule_date_end = request.POST.get('schedule_end')
            maintenance_type = request.POST.get('type')
            new_maintenance = Maintenance(schedule_start=schedule_date_start, schedule_end=schedule_date_end, created_by=current_user, maintenance_type=maintenance_type)
            new_maintenance.save()
            return JsonResponse({
                'result': True,
            })
        else:
            if request.POST.get('is_predemo') == 'true':
                is_predemo = True
            else:
                is_predemo = False
            order_id = request.POST.get('order_id')
            order = Order.objects.get(id=order_id)
            if is_predemo:
                if not ProjectProcessPreDemo.objects.filter(order=order).exists():
                    ProjectProcessPreDemo.objects.create(order=order)
                order.projectprocesspredemo.tech_package = True
                order.projectprocesspredemo.tech_scheduled = True
                order.projectprocesspredemo.save()
            else:
                if not ProjectProcess.objects.filter(order=order).exists():
                    ProjectProcess.objects.create(order=order)
                order.projectprocess.tech_package = True
                order.projectprocess.tech_scheduled = True
                order.projectprocess.save()
            schedule_date_end = request.POST.get('schedule_end')
            schedule_date_start = request.POST.get('schedule_start')
            current_user = request.user
            new_schedule = Schedule(order=order, schedule_start=schedule_date_start, schedule_end=schedule_date_end,
                                    created_by=current_user, pre_demo=is_predemo)
            new_schedule.save()
            return JsonResponse({
                'result': True,
                'schedule_id': new_schedule.id
            })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


@login_required
def update_schedule(request):
    if request.method == "POST" and request.is_ajax():
        update_type = request.POST.get('type')
        order_id = request.POST.get('org_order_id')
        schedule_id = request.POST.get('schedule_id')
        schedule_update = get_object_or_404(Schedule, id=schedule_id)
        new_tech_id = request.POST.get('new_tech_id')
        if update_type == 'calendar_delete':
            if schedule_update.pre_demo:
                is_predemo = True
            else:
                is_predemo = False
            schedule_update.delete()
            other_schedules = Schedule.objects.filter(order__id=order_id, pre_demo=is_predemo)
            no_schedule_left = False
            if not other_schedules:
                if is_predemo:
                    schedule_update.order.projectprocesspredemo.tech_scheduled = False
                    schedule_update.order.projectprocesspredemo.save()
                    no_schedule_left = True
                else:
                    schedule_update.order.projectprocess.tech_scheduled = False
                    schedule_update.order.projectprocess.save()
                    no_schedule_left = True
            return JsonResponse({
                'result': True,
                'no_schedule_left': no_schedule_left,
                'is_predemo': is_predemo,
                'msg': 'Schedule Deleted from database successfully.'
            })
        else:
            if update_type == 'tech_add':
                this_schedule = Schedule.objects.get(id=schedule_id)
                new_date = this_schedule.schedule_start
                new_date_end = this_schedule.schedule_end
                start_check = new_date - timedelta(minutes=29)
                end_check = new_date_end + timedelta(minutes=29)
                if request.POST.get('tech_type') == 'employee':
                    has_conflict = False
                    conflicted_user = 0
                    conflicted_type = None
                    this_tech_schedules = ScheduleTech.objects.filter(Q(assigned_to_employee__id=new_tech_id,
                                                                        schedule__schedule_start__lt=start_check,
                                                                        schedule__schedule_end__gt=start_check) |
                                                                      Q(assigned_to_employee__id=new_tech_id,
                                                                        schedule__schedule_start__gt=start_check,
                                                                        schedule__schedule_start__lt=end_check)).exclude(schedule=this_schedule)
                    maintenance_conflict = Maintenance.objects.filter(
                        Q(assigned_to_employee__id=new_tech_id,
                          schedule_start__lt=start_check,
                          schedule_end__gt=start_check) |
                        Q(assigned_to_employee__id=new_tech_id,
                          schedule_start__gt=start_check,
                          schedule_start__lt=end_check))
                    if this_tech_schedules or maintenance_conflict:
                        has_conflict = True
                        conflicted_user = new_tech_id
                        conflicted_type = 'employee'
                    err_msg = ''
                    if has_conflict:
                        if conflicted_type == 'employee':
                            conflicted_user = User.objects.get(id=conflicted_user)
                            if conflicted_user.last_name:
                                err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                            else:
                                err_msg = conflicted_user.email + ' has another job to do on this date.'
                            return JsonResponse({
                                'result': False,
                                'err_msg': err_msg
                            })
                    assigned_count = ScheduleTech.objects.filter(schedule=this_schedule,
                                                                 assigned_to_employee=new_tech_id).count()
                    if assigned_count == 0:
                        new_tech_schedule = ScheduleTech(schedule=this_schedule,
                                                         assigned_to_employee=User.objects.get(id=new_tech_id))
                        new_tech_schedule.save()
                elif request.POST.get('tech_type') == 'contractor':
                    has_conflict = False
                    conflicted_user = 0
                    conflicted_type = None
                    this_tech_schedules = ScheduleTech.objects.filter(Q(assigned_to_contractor__id=new_tech_id,
                                                                        schedule__schedule_start__lt=start_check,
                                                                        schedule__schedule_end__gt=start_check) |
                                                                      Q(assigned_to_contractor__id=new_tech_id,
                                                                        schedule__schedule_start__gt=start_check,
                                                                        schedule__schedule_start__lt=end_check)).exclude(schedule=this_schedule)
                    maintenance_conflict = Maintenance.objects.filter(
                        Q(assigned_to_contractor__id=new_tech_id,
                          schedule_start__lt=start_check,
                          schedule_end__gt=start_check) |
                        Q(assigned_to_contractor__id=new_tech_id,
                          schedule_start__gt=start_check,
                          schedule_start__lt=end_check))
                    if this_tech_schedules or maintenance_conflict:
                        has_conflict = True
                        conflicted_user = new_tech_id
                        conflicted_type = 'contractor'
                    err_msg = ''
                    if has_conflict:
                        if conflicted_type == 'contractor':
                            conflicted_user = User.objects.get(id=conflicted_user)
                            if conflicted_user.last_name:
                                err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                            else:
                                err_msg = conflicted_user.email + ' has another job to do on this date.'
                            return JsonResponse({
                                'result': False,
                                'err_msg': err_msg
                            })
                    assigned_count = ScheduleTech.objects.filter(schedule=this_schedule,
                                                                 assigned_to_contractor=new_tech_id).count()
                    if assigned_count == 0:
                        new_tech_schedule = ScheduleTech(schedule=this_schedule,
                                                         assigned_to_contractor=User.objects.get(id=new_tech_id))
                        new_tech_schedule.save()

                all_tech_schedules = ScheduleTech.objects.filter(schedule=this_schedule)
                remain_percentage = 100
                total_techs = all_tech_schedules.count()
                rounded_mean = int(remain_percentage / total_techs)
                for tech_schedule in all_tech_schedules.all():
                    if tech_schedule == all_tech_schedules.last():
                        tech_schedule.involvement_percentage = remain_percentage
                        tech_schedule.save()
                        remain_percentage = remain_percentage - rounded_mean

                    else:
                        tech_schedule.involvement_percentage = rounded_mean
                        tech_schedule.save()
                        remain_percentage = remain_percentage - rounded_mean

            elif update_type == 'tech_remove':
                if request.POST.get('tech_type') == 'employee':
                    ScheduleTech.objects.get(schedule=schedule_update, assigned_to_employee=new_tech_id).delete()
                elif request.POST.get('tech_type') == 'contractor':
                    ScheduleTech.objects.get(schedule=schedule_update, assigned_to_contractor=new_tech_id).delete()
                this_schedule = Schedule.objects.get(id=schedule_id)
                all_tech_schedules = ScheduleTech.objects.filter(schedule=this_schedule)
                if all_tech_schedules:
                    remain_percentage = 100
                    total_techs = all_tech_schedules.count()
                    rounded_mean = int(remain_percentage / total_techs)
                    for tech_schedule in all_tech_schedules.all():
                        if tech_schedule == all_tech_schedules.last():
                            tech_schedule.involvement_percentage = remain_percentage
                            tech_schedule.save()
                            remain_percentage = remain_percentage - rounded_mean

                        else:
                            tech_schedule.involvement_percentage = rounded_mean
                            tech_schedule.save()
                            remain_percentage = remain_percentage - rounded_mean
                return JsonResponse({
                    'result': True
                })
            elif update_type == 'update_percentages':
                schedule_techs = ScheduleTech.objects.filter(schedule=schedule_update)
                techs_array = request.POST.get('techs')
                techs_array = json.loads(techs_array)
                for tech in techs_array:
                    if tech['type'] == 'employee':
                        this_schedule_tech = ScheduleTech.objects.get(schedule=schedule_update,
                                                                      assigned_to_employee__id=int(tech['id']))
                        this_schedule_tech.involvement_percentage = int(tech['new_percentage'])
                        this_schedule_tech.save()
                    elif tech['type'] == 'contractor':
                        this_schedule_tech = ScheduleTech.objects.get(schedule=schedule_update,
                                                                      assigned_to_contractor__id=int(tech['id']))
                        this_schedule_tech.involvement_percentage = int(tech['new_percentage'])
                        this_schedule_tech.save()
                return JsonResponse({
                    'result': True
                })
            elif update_type == 'calendar_update':
                this_schedule = Schedule.objects.get(id=schedule_id)
                all_schedule_techs = ScheduleTech.objects.filter(schedule=this_schedule)
                new_date = request.POST.get('new_date')
                new_date_end = request.POST.get('new_date_end')
                start_check = parse_datetime(new_date) - timedelta(minutes=29)
                end_check = parse_datetime(new_date_end) + timedelta(minutes=29)
                has_conflict = False
                conflicted_user = 0
                conflicted_type = None
                for schedule_tech in all_schedule_techs.all():
                    if schedule_tech.assigned_to_employee:
                        this_schedule_techs = ScheduleTech.objects.filter(
                            Q(assigned_to_employee__id=schedule_tech.assigned_to_employee.id,
                              schedule__schedule_start__lt=start_check,
                              schedule__schedule_end__gt=start_check) |
                            Q(assigned_to_employee__id=schedule_tech.assigned_to_employee.id,
                              schedule__schedule_start__gt=start_check,
                              schedule__schedule_start__lt=end_check)).exclude(schedule=this_schedule)
                        maintenance_conflict = Maintenance.objects.filter(
                            Q(assigned_to_employee__id=schedule_tech.assigned_to_employee.id,
                              schedule_start__lt=start_check,
                              schedule_end__gt=start_check) |
                            Q(assigned_to_employee__id=schedule_tech.assigned_to_employee.id,
                              schedule_start__gt=start_check,
                              schedule_start__lt=end_check))
                        if this_schedule_techs or maintenance_conflict:
                            has_conflict = True
                            conflicted_user = schedule_tech.assigned_to_employee.id
                            conflicted_type = 'employee'
                    elif schedule_tech.assigned_to_contractor:
                        this_schedule_techs = ScheduleTech.objects.filter(
                            Q(assigned_to_contractor__id=schedule_tech.assigned_to_contractor.id,
                              schedule__schedule_start__lt=start_check,
                              schedule__schedule_end__gt=start_check) |
                            Q(assigned_to_contractor__id=schedule_tech.assigned_to_contractor.id,
                              schedule__schedule_start__gt=start_check,
                              schedule__schedule_start__lt=end_check)).exclude(schedule=this_schedule)
                        maintenance_conflict = Maintenance.objects.filter(
                            Q(assigned_to_contractor__id=schedule_tech.assigned_to_contractor.id,
                              schedule_start__lt=start_check,
                              schedule_end__gt=start_check) |
                            Q(assigned_to_contractor__id=schedule_tech.assigned_to_contractor.id,
                              schedule_start__gt=start_check,
                              schedule_start__lt=end_check))
                        if this_schedule_techs or maintenance_conflict:
                            has_conflict = True
                            conflicted_user = schedule_tech.assigned_to_contractor.id
                            conflicted_type = 'contractor'

                err_msg = ''
                if has_conflict:
                    if conflicted_type == 'contractor':
                        conflicted_user = User.objects.get(id=conflicted_user)
                        if conflicted_user.last_name:
                            err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                        else:
                            err_msg = conflicted_user.email + ' has another job to do on this date.'
                    elif conflicted_type == 'employee':
                        conflicted_user = User.objects.get(id=conflicted_user)
                        if conflicted_user.last_name:
                            err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                        else:
                            err_msg = conflicted_user.email + ' has another job to do on this date.'
                    return JsonResponse({
                        'result': False,
                        'err_msg': err_msg
                    })
                schedule_update.schedule_start = new_date
                schedule_update.schedule_end = new_date_end
                schedule_update.save()
            return JsonResponse({
                'result': True,
                'msg': 'Schedule updated on database successfully.'
            })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


@login_required
def update_maintenance(request):
    if request.method == "POST" and request.is_ajax():
        update_type = request.POST.get('type')
        order_id = request.POST.get('org_order_id')
        maintenance_id = request.POST.get('maintenance_id')
        schedule_update = get_object_or_404(Maintenance, id=maintenance_id)
        new_tech_id = request.POST.get('new_tech_id')
        if update_type == 'calendar_delete':
            schedule_update.delete()
            return JsonResponse({
                'result': True,
                'msg': 'Schedule Deleted from database successfully.'
            })
        else:
            if update_type == 'tech_add':
                this_maintenance = Maintenance.objects.get(id=maintenance_id)
                new_date = this_maintenance.schedule_start
                new_date_end = this_maintenance.schedule_end
                start_check = new_date - timedelta(minutes=29)
                end_check = new_date_end + timedelta(minutes=29)
                if request.POST.get('tech_type') == 'employee':
                    has_conflict = False
                    conflicted_user = 0
                    conflicted_type = None
                    this_tech_schedules = ScheduleTech.objects.filter(Q(assigned_to_employee__id=new_tech_id,
                                                                        schedule__schedule_start__lt=start_check,
                                                                        schedule__schedule_end__gt=start_check) |
                                                                      Q(assigned_to_employee__id=new_tech_id,
                                                                        schedule__schedule_start__gt=start_check,
                                                                        schedule__schedule_start__lt=end_check))

                    maintenance_conflict = Maintenance.objects.filter(
                        Q(assigned_to_employee__id=new_tech_id,
                          schedule_start__lt=start_check,
                          schedule_end__gt=start_check) |
                        Q(assigned_to_employee__id=new_tech_id,
                          schedule_start__gt=start_check,
                          schedule_start__lt=end_check)).exclude(id=this_maintenance.id)
                    if this_tech_schedules or maintenance_conflict:
                        has_conflict = True
                        conflicted_user = new_tech_id
                        conflicted_type = 'employee'
                    err_msg = ''
                    if has_conflict:
                        if conflicted_type == 'employee':
                            conflicted_user = User.objects.get(id=conflicted_user)
                            if conflicted_user.last_name:
                                err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                            else:
                                err_msg = conflicted_user.email + ' has another job to do on this date.'
                            return JsonResponse({
                                'result': False,
                                'err_msg': err_msg
                            })
                    new_tech_maintenance = Maintenance.objects.get(id=maintenance_id)
                    new_tech_maintenance.assigned_to_contractor = None
                    new_tech_maintenance.assigned_to_employee = User.objects.get(id=new_tech_id)
                    new_tech_maintenance.save()
                elif request.POST.get('tech_type') == 'contractor':
                    has_conflict = False
                    conflicted_user = 0
                    conflicted_type = None
                    this_tech_schedules = ScheduleTech.objects.filter(Q(assigned_to_contractor__id=new_tech_id,
                                                                        schedule__schedule_start__lt=start_check,
                                                                        schedule__schedule_end__gt=start_check) |
                                                                      Q(assigned_to_contractor__id=new_tech_id,
                                                                        schedule__schedule_start__gt=start_check,
                                                                        schedule__schedule_start__lt=end_check))
                    maintenance_conflict = Maintenance.objects.filter(
                        Q(assigned_to_contractor__id=new_tech_id,
                          schedule_start__lt=start_check,
                          schedule_end__gt=start_check) |
                        Q(assigned_to_contractor__id=new_tech_id,
                          schedule_start__gt=start_check,
                          schedule_start__lt=end_check)).exclude(id=this_maintenance.id)
                    if this_tech_schedules or maintenance_conflict:
                        has_conflict = True
                        conflicted_user = new_tech_id
                        conflicted_type = 'contractor'
                    err_msg = ''
                    if has_conflict:
                        if conflicted_type == 'contractor':
                            conflicted_user = User.objects.get(id=conflicted_user)
                            if conflicted_user.last_name:
                                err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                            else:
                                err_msg = conflicted_user.email + ' has another job to do on this date.'
                            return JsonResponse({
                                'result': False,
                                'err_msg': err_msg
                            })
                    new_tech_maintenance = Maintenance.objects.get(id=maintenance_id)
                    new_tech_maintenance.assigned_to_employee = None
                    new_tech_maintenance.assigned_to_contractor = User.objects.get(id=new_tech_id)
                    new_tech_maintenance.save()

            elif update_type == 'update_order':
                this_maintenance = Maintenance.objects.get(id=maintenance_id)
                maintenance_type = request.POST.get('maintenance_type')
                if maintenance_type != '3':
                    this_maintenance.order = Order.objects.get(id=order_id)
                this_maintenance.description = request.POST.get('desc')
                this_maintenance.save()
                return JsonResponse({
                    'result': True
                })

            elif update_type == 'calendar_update':
                this_maintenance = Maintenance.objects.get(id=maintenance_id)
                new_date = request.POST.get('new_date')
                new_date_end = request.POST.get('new_date_end')
                start_check = parse_datetime(new_date) - timedelta(minutes=29)
                end_check = parse_datetime(new_date_end) + timedelta(minutes=29)
                has_conflict = False
                conflicted_user = 0
                conflicted_type = None
                if this_maintenance.assigned_to_employee:
                    this_schedule_techs = ScheduleTech.objects.filter(
                        Q(assigned_to_employee__id=this_maintenance.assigned_to_employee.id,
                          schedule__schedule_start__lt=start_check,
                          schedule__schedule_end__gt=start_check) |
                        Q(assigned_to_employee__id=this_maintenance.assigned_to_employee.id,
                          schedule__schedule_start__gt=start_check,
                          schedule__schedule_start__lt=end_check))
                    maintenance_conflict = Maintenance.objects.filter(
                        Q(assigned_to_employee__id=this_maintenance.assigned_to_employee.id,
                          schedule_start__lt=start_check,
                          schedule_end__gt=start_check) |
                        Q(assigned_to_employee__id=this_maintenance.assigned_to_employee.id,
                          schedule_start__gt=start_check,
                          schedule_start__lt=end_check)).exclude(id=this_maintenance.id)
                    if this_schedule_techs or maintenance_conflict:
                        has_conflict = True
                        conflicted_user = this_maintenance.assigned_to_employee.id
                        conflicted_type = 'employee'
                elif this_maintenance.assigned_to_contractor:
                    this_schedule_techs = ScheduleTech.objects.filter(
                        Q(assigned_to_contractor__id=this_maintenance.assigned_to_contractor.id,
                          schedule__schedule_start__lt=start_check,
                          schedule__schedule_end__gt=start_check) |
                        Q(assigned_to_contractor__id=this_maintenance.assigned_to_contractor.id,
                          schedule__schedule_start__gt=start_check,
                          schedule__schedule_start__lt=end_check))
                    maintenance_conflict = Maintenance.objects.filter(
                        Q(assigned_to_contractor__id=this_maintenance.assigned_to_contractor.id,
                          schedule_start__lt=start_check,
                          schedule_end__gt=start_check) |
                        Q(assigned_to_contractor__id=this_maintenance.assigned_to_contractor.id,
                          schedule_start__gt=start_check,
                          schedule_start__lt=end_check)).exclude(id=this_maintenance.id)
                    if this_schedule_techs or maintenance_conflict:
                        has_conflict = True
                        conflicted_user = this_maintenance.assigned_to_contractor.id
                        conflicted_type = 'contractor'

                err_msg = ''
                if has_conflict:
                    if conflicted_type == 'contractor':
                        conflicted_user = User.objects.get(id=conflicted_user)
                        if conflicted_user.last_name:
                            err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                        else:
                            err_msg = conflicted_user.email + ' has another job to do on this date.'
                    elif conflicted_type == 'employee':
                        conflicted_user = User.objects.get(id=conflicted_user)
                        if conflicted_user.last_name:
                            err_msg = conflicted_user.first_name + ' ' + conflicted_user.last_name + ' has another job to do on this date.'
                        else:
                            err_msg = conflicted_user.email + ' has another job to do on this date.'
                    return JsonResponse({
                        'result': False,
                        'err_msg': err_msg
                    })
                schedule_update.schedule_start = new_date
                schedule_update.schedule_end = new_date_end
                schedule_update.save()
            return JsonResponse({
                'result': True,
                'msg': 'Maintenance updated on database successfully.'
            })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


@login_required
def get_schedule_info(request, schedule_id):
    if request.method == "POST" and request.is_ajax():
        this_schedule = Schedule.objects.get(id=schedule_id)
        techs_array = []
        schedule_techs = ScheduleTech.objects.filter(schedule=this_schedule)
        for schedule_tech in schedule_techs:
            if schedule_tech.assigned_to_employee:
                if schedule_tech.assigned_to_employee.last_name:
                    tech_name = schedule_tech.assigned_to_employee.first_name + ' ' + schedule_tech.assigned_to_employee.last_name
                else:
                    tech_name = schedule_tech.assigned_to_employee.email
                techs_array.append({
                    'tech_id': schedule_tech.assigned_to_employee.id,
                    'tech_name': tech_name,
                    'tech_type': 'employee',
                    'involvement_percentage': schedule_tech.involvement_percentage
                })
            elif schedule_tech.assigned_to_contractor:
                if schedule_tech.assigned_to_contractor.last_name:
                    tech_name = schedule_tech.assigned_to_contractor.first_name + ' ' + schedule_tech.assigned_to_contractor.last_name
                else:
                    tech_name = schedule_tech.assigned_to_contractor.email
                techs_array.append({
                    'tech_id': schedule_tech.assigned_to_contractor.id,
                    'tech_name': tech_name,
                    'tech_type': 'contractor',
                    'involvement_percentage': schedule_tech.involvement_percentage
                })
        return JsonResponse({
            'result': True,
            'techs': techs_array
        })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


@login_required
def get_maintenance_info(request, maintenance_id):
    if request.method == "POST" and request.is_ajax():
        this_maintenance = Maintenance.objects.get(id=maintenance_id)
        techs_array = []
        if this_maintenance.assigned_to_employee:
            if this_maintenance.assigned_to_employee.last_name:
                tech_name = this_maintenance.assigned_to_employee.first_name + ' ' + this_maintenance.assigned_to_employee.last_name
            else:
                tech_name = this_maintenance.assigned_to_employee.email
            techs_array.append({
                'tech_id': this_maintenance.assigned_to_employee.id,
                'tech_name': tech_name,
                'tech_type': 'employee',
            })
        elif this_maintenance.assigned_to_contractor:
            if this_maintenance.assigned_to_contractor.last_name:
                tech_name = this_maintenance.assigned_to_contractor.first_name + ' ' + this_maintenance.assigned_to_contractor.last_name
            else:
                tech_name = this_maintenance.assigned_to_contractor.email
            techs_array.append({
                'tech_id': this_maintenance.assigned_to_contractor.id,
                'tech_name': tech_name,
                'tech_type': 'contractor',
            })
        return JsonResponse({
            'result': True,
            'type': this_maintenance.maintenance_type,
            'techs': techs_array,
            'desc': this_maintenance.description
        })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)

from platform import system

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.mail import BadHeaderError, EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.order.models import Order
from .forms import SettlementForm, SettledScheduleForm
from .models import Settlement, SettledSchedule, ModulesToEmailTemplateRelation, SettledMaintenances
from ..core.forms import EmailForm
from ..core.views import htmlbodytemplate_tag_converter
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, DEFAULT_FROM_EMAIL
from ..scheduler.models import *
import datetime
from ..gi.views import order_total_calculator


# Create your views here.

@login_required
def settlement_list(request):
    form = EmailForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            to_email = to_email.replace(" ", "").replace(";", ",").split(',')
            cc = form.cleaned_data['cc']
            cc = cc.replace(" ", "").replace(";", ",").split(',')
            email_id = form.cleaned_data['email_id']
            subject = form.cleaned_data['subject']
            this_settlement = get_object_or_404(Settlement, id=email_id)
            customer = this_settlement.contractor
            if ModulesToEmailTemplateRelation.objects.filter(module=8).exists():
                body_content = get_object_or_404(ModulesToEmailTemplateRelation, module=8).template.content
            else:
                body_content = "There was no email template defined for 'Settlement'."
            body_content = htmlbodytemplate_tag_converter(1, body_content, request, customer)
            if ModulesToEmailTemplateRelation.objects.filter(module=5).exists():
                footer_content = ModulesToEmailTemplateRelation.objects.get(module=5).template.content
            else:
                footer_content = "There was no email template defined for 'Email Footer'."
            footer_content = htmlbodytemplate_tag_converter(1, footer_content, request, customer)
            message = body_content + '<br />' + footer_content
            try:
                msg = EmailMessage(
                    subject,
                    message,
                    DEFAULT_FROM_EMAIL,
                    to_email,
                    cc=cc,
                )
                msg.content_subtype = "html"
                msg.attach_file('media/pdfs/settlement/settlement-' + str(email_id) + '.pdf')
                msg.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('settlementHome')

    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Settlement.objects.filter(Q(contractor__first_name__icontains=search) | Q(contractor__last_name__icontains=search)) \
        .order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    settlements = paginator.get_page(page)

    must_go = Settlement.objects.filter(settledschedule__isnull=True)
    must_go.delete()

    parameters = {'settlements': settlements,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'form': form,
                  }
    return render(request, "settlement.html", parameters)


@login_required
def settlement_add(request):
    form = SettlementForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('settlementHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                new_settlement = form.save()
                return redirect('settlementOrders', new_settlement.pk)
    parameters = {'form': form,
                  }
    return render(request, "settlementAdd.html", parameters)


@login_required
def settlement_orders(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    form = SettledScheduleForm(request.POST or None, request.FILES or None, initial={'settlement': this_settlement.id})
    schedules = Schedule.objects.filter(scheduletech__assigned_to_contractor=this_settlement.contractor, scheduletech__settlement=False).filter(schedule_start__gt=this_settlement.settlement_start, schedule_end__lt=this_settlement.settlement_end).order_by('-created_on').distinct()
    maintenances = Maintenance.objects.filter(assigned_to_contractor=this_settlement.contractor, settlement=False).filter(schedule_start__gt=this_settlement.settlement_start, schedule_end__lt=this_settlement.settlement_end).order_by('-created_on').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            this_settlement.delete()
            return redirect('settlementHome')
        if request.POST.get("next"):
            for schedule in schedules:
                total_settled_value = 0
                total_schedules_duration = 0
                quoted_price = 0
                prev_payment = None
                if request.POST.get("order-include-" + str(schedule.id)):
                    if request.POST.get("or-toggle-" + str(schedule.id)):
                        settled_type = True
                        project_this_period_percentage = int(request.POST.get("percentage-" + str(schedule.id)))
                        if schedule.pre_demo:
                            schedule.order.pre_demo_completion_percentage = schedule.order.pre_demo_completion_percentage + project_this_period_percentage
                        else:
                            schedule.order.completion_percentage = schedule.order.completion_percentage + project_this_period_percentage
                        schedule.order.save()
                        schedule_tech = ScheduleTech.objects.get(schedule=schedule,
                                                                 assigned_to_contractor=this_settlement.contractor)
                        schedule_duration_in_hours = ((schedule.schedule_end - schedule.schedule_start).total_seconds()) / 3600
                        total_schedules_duration = total_schedules_duration + schedule_duration_in_hours
                        if request.POST.get("quoted-price-" + str(schedule.id)):
                            override_quoted_price = float(request.POST.get("quoted-price-" + str(schedule.id)))
                            quoted_price = override_quoted_price
                        else:
                            quoted_price = float(order_total_calculator(schedule.order.proposal.quote.estimate.id, schedule.order))
                        settle_value = (project_this_period_percentage / 100 * float(this_settlement.contractor.profile.interest_percentage) / 100 * quoted_price) * schedule_tech.involvement_percentage / 100
                        total_settled_value = total_settled_value + round(settle_value, 2)
                        schedule_tech.settlement = True
                        schedule_tech.save()
                    else:
                        settled_type = False
                        project_this_period_percentage = int(request.POST.get("percentage-" + str(schedule.id)))
                        if schedule.pre_demo:
                            schedule.order.pre_demo_completion_percentage = schedule.order.pre_demo_completion_percentage + project_this_period_percentage
                        else:
                            schedule.order.completion_percentage = schedule.order.completion_percentage + project_this_period_percentage
                        schedule.order.save()
                        schedule_tech = ScheduleTech.objects.get(schedule=schedule,
                                                                 assigned_to_contractor=this_settlement.contractor)
                        if request.POST.get("total-hour-" + str(schedule.id)):
                            override_total_duration = float(request.POST.get("total-hour-" + str(schedule.id)))
                            schedule_duration_in_hours = override_total_duration
                        else:
                            schedule_duration_in_hours = ((schedule.schedule_end - schedule.schedule_start).total_seconds()) / 3600
                        total_schedules_duration = total_schedules_duration + schedule_duration_in_hours
                        settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(schedule_duration_in_hours)
                        total_settled_value = total_settled_value + round(settle_value, 2)
                        schedule_tech.settlement = True
                        schedule_tech.save()
                    if request.POST.get("pp-" + str(schedule.id)):
                        prev_payment = request.POST.get("pp-" + str(schedule.id))
                    settled_schedule = SettledSchedule(settlement=this_settlement, schedule=schedule,
                                                       settled_total=quoted_price,
                                                       settled_value=total_settled_value,
                                                       settled_type=settled_type, settled_hours=total_schedules_duration,
                                                       completion_percentage=project_this_period_percentage,
                                                       previous_payment=prev_payment)
                    settled_schedule.save()
            for maintenance in maintenances:
                total_settled_value = 0
                total_schedules_duration = 0
                if request.POST.get("maintenance-include-" + str(maintenance.id)):
                    schedule = Maintenance.objects.get(order=maintenance.order, assigned_to_contractor=this_settlement.contractor)
                    if request.POST.get("maintenance-total-hour-" + str(maintenance.id)):
                        override_total_duration = float(request.POST.get("maintenance-total-hour-" + str(maintenance.id)))
                        schedule_duration_in_hours = override_total_duration
                    else:
                        schedule_duration_in_hours = ((schedule.schedule_end - schedule.schedule_start).total_seconds()) / 3600
                    total_schedules_duration = total_schedules_duration + schedule_duration_in_hours
                    settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(schedule_duration_in_hours)
                    total_settled_value = total_settled_value + round(settle_value, 2)
                    schedule.settlement = True
                    schedule.save()
                settled_maintenance = SettledMaintenances(settlement=this_settlement, maintenance=maintenance, settled_value=total_settled_value, settled_hours=total_schedules_duration)
                settled_maintenance.save()
            return redirect('settlementView', this_settlement.id)
    parameters = {'form': form,
                  'this_settlement': this_settlement,
                  'schedules': schedules,
                  'maintenances': maintenances,
                  }
    return render(request, "settlementOrders.html", parameters)


@login_required
def settlement_edit(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    form = SettledScheduleForm(request.POST or None, request.FILES or None, initial={'settlement': this_settlement.id})
    schedules = SettledSchedule.objects.filter(settlement_id=settlement_id)
    maintenances = SettledMaintenances.objects.filter(settlement_id=settlement_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('settlementHome')
        if request.POST.get("next"):
            for schedule in schedules:
                total_settled_value = 0
                total_schedules_duration = 0
                quoted_price = 0
                prev_payment = None
                if request.POST.get("or-toggle-" + str(schedule.id)):
                    settled_type = True
                    project_this_period_percentage = int(request.POST.get("percentage-" + str(schedule.id)))
                    if schedule.schedule.pre_demo:
                        schedule.schedule.order.pre_demo_completion_percentage = schedule.schedule.order.pre_demo_completion_percentage + project_this_period_percentage - schedule.completion_percentage
                    else:
                        schedule.schedule.order.completion_percentage = schedule.schedule.order.completion_percentage + project_this_period_percentage - schedule.completion_percentage
                    schedule.schedule.order.save()
                    schedule_tech = ScheduleTech.objects.get(schedule=schedule.schedule,
                                                             assigned_to_contractor=this_settlement.contractor)
                    override_quoted_price = float(request.POST.get("quoted-price-" + str(schedule.id)))
                    quoted_price = override_quoted_price
                    settle_value = (project_this_period_percentage / 100 * float(this_settlement.contractor.profile.interest_percentage) / 100 * quoted_price) * schedule_tech.involvement_percentage / 100
                    total_settled_value = total_settled_value + round(settle_value, 2)
                else:
                    settled_type = False
                    project_this_period_percentage = int(request.POST.get("percentage-" + str(schedule.id)))
                    if schedule.schedule.pre_demo:
                        schedule.schedule.order.pre_demo_completion_percentage = schedule.schedule.order.pre_demo_completion_percentage + project_this_period_percentage - schedule.completion_percentage
                    else:
                        schedule.schedule.order.completion_percentage = schedule.schedule.order.completion_percentage + project_this_period_percentage - schedule.completion_percentage
                    schedule.schedule.order.save()
                    override_total_duration = float(request.POST.get("total-hour-" + str(schedule.id)))
                    total_schedules_duration = override_total_duration
                    schedule.settled_hours = total_schedules_duration
                    settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(total_schedules_duration)
                    total_settled_value = total_settled_value + round(settle_value, 2)
                if request.POST.get("pp-" + str(schedule.id)):
                    prev_payment = request.POST.get("pp-" + str(schedule.id))
                schedule.settled_total = quoted_price
                schedule.settled_value = total_settled_value
                schedule.settled_type = settled_type
                schedule.completion_percentage = project_this_period_percentage
                schedule.previous_payment = prev_payment
                schedule.save()
            for maintenance in maintenances:
                override_total_duration = float(request.POST.get("maintenance-total-hour-" + str(maintenance.id)))
                total_schedules_duration = override_total_duration
                settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(total_schedules_duration)
                maintenance.settled_value = settle_value
                maintenance.settled_hours = total_schedules_duration
                maintenance.save()
            return redirect('settlementView', this_settlement.id)
    parameters = {'form': form,
                  'this_settlement': this_settlement,
                  'schedules': schedules,
                  'maintenances': maintenances,
                  }
    return render(request, "settlementEdit.html", parameters)



@login_required
def settlement_view(request, settlement_id):
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value
    settlement = Settlement.objects.get(id=settlement_id)
    settled_schedules = SettledSchedule.objects.filter(settlement=settlement).order_by('schedule__schedule_start')
    settled_maintenances = SettledMaintenances.objects.filter(settlement=settlement)
    settlement_id_prefix = settlement.settlement_start.strftime("%y%m")

    parameters = {'file_name': 'settlement-' + str(settlement_id),
                  'settlement': settlement,
                  'settled_schedules': settled_schedules,
                  'settled_maintenances': settled_maintenances,
                  'datetime': datetime.datetime.now(),
                  'license_owner': license_owner,
                  'owner_title': owner_title,
                  'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
                  'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
                  'owner_tel': owner_tel,
                  'owner_fax': owner_fax,
                  'owner_web': owner_web,
                  'owner_mail': owner_mail,
                  'owner_signature': owner_signature,
                  'owner_logo': owner_logo,
                  'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                  'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                  'company_name': company_name,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'STATIC_URL': STATIC_URL,
                  'os': system(),
                  'settlement_id_prefix': settlement_id_prefix,
                  }
    settlement_pdf = Settlement.create_settlement_pdf(parameters)
    parameters['settlement_pdf'] = settlement_pdf[1]
    return render(request, "settlementView.html", parameters)


@login_required
def settlement_delete(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            for settled_schedule in this_settlement.settledschedule_set.all():
                settled_schedule.schedule.order.fully_settled = False
                if settled_schedule.schedule.pre_demo:
                    settled_schedule.schedule.order.pre_demo_completion_percentage = settled_schedule.schedule.order.pre_demo_completion_percentage - settled_schedule.completion_percentage
                else:
                    settled_schedule.schedule.order.completion_percentage = settled_schedule.schedule.order.completion_percentage - settled_schedule.completion_percentage
                settled_schedule.schedule.order.save()
                schedule_tech = ScheduleTech.objects.get(schedule=settled_schedule.schedule, assigned_to_contractor=this_settlement.contractor)
                schedule_tech.settlement = False
                schedule_tech.save()
            for settled_maintenance in this_settlement.settledmaintenances_set.all():
                settled_maintenance.maintenance.settlement = False
                settled_maintenance.maintenance.save()
            this_settlement.delete()
        return redirect('settlementHome')
    parameters = {'this_settlement': this_settlement
                  }
    return render(request, "settlementDelete.html", parameters)

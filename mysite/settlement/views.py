from platform import system
import os
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
from django.conf import settings
from ..scheduler.models import *
import datetime
from ..gi.views import order_total_calculator, estimate_predemo_calculator
from .render import Render as PDFRender


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
                    settings.DEFAULT_FROM_EMAIL,
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

    # must_go = Settlement.objects.filter(settledschedule__isnull=True, settledmaintenances__isnull=True)
    # must_go.delete()

    parameters = {'settlements': settlements,
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
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
                new_settlement.settlement_end = new_settlement.settlement_end + datetime.timedelta(hours=23, minutes=59, seconds=59)
                new_settlement.save()
                return redirect('settlementOrders', new_settlement.pk)
    parameters = {'form': form,
                  }
    return render(request, "settlementAdd.html", parameters)


@login_required
def settlement_orders(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    form = SettledScheduleForm(request.POST or None, request.FILES or None, initial={'settlement': this_settlement.id})
    schedules = Schedule.objects.filter(scheduletech__assigned_to_contractor=this_settlement.contractor, scheduletech__settlement=False).filter(schedule_start__gt=this_settlement.settlement_start, schedule_end__lt=this_settlement.settlement_end).distinct().order_by('schedule_start')
    maintenances = Maintenance.objects.filter(assigned_to_contractor=this_settlement.contractor, settlement=False).filter(schedule_start__gt=this_settlement.settlement_start, schedule_end__lt=this_settlement.settlement_end).filter(Q(maintenance_type=1) | Q(maintenance_type=2)).order_by('-created_on').distinct().order_by('schedule_start')
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
                completion_percentage = None
                if request.POST.get("order-include-" + str(schedule.id)):
                    if request.POST.get("pp-" + str(schedule.id)):
                        prev_payment = request.POST.get("pp-" + str(schedule.id))
                    if request.POST.get("or-toggle-" + str(schedule.id)):
                        order_schedules = Schedule.objects.filter(order=schedule.order, pre_demo=schedule.pre_demo)
                        order_total_scheduled = 0
                        for order_schedule in order_schedules:
                            order_total_scheduled += ((order_schedule.schedule_end - order_schedule.schedule_start).total_seconds()) / 3600
                        settled_type = True
                        if schedule.pre_demo:
                            schedule.order.pre_demo_completion_percentage = 100
                        else:
                            schedule.order.completion_percentage = 100
                        schedule.order.save()
                        schedule_tech = ScheduleTech.objects.get(schedule=schedule,
                                                                 assigned_to_contractor=this_settlement.contractor)
                        schedule_duration_in_hours = ((schedule.schedule_end - schedule.schedule_start).total_seconds()) / 3600
                        total_schedules_duration = total_schedules_duration + schedule_duration_in_hours

                        completion_percentage = round(total_schedules_duration / order_total_scheduled * 100)

                        if request.POST.get("quoted-price-" + str(schedule.id)):
                            override_quoted_price = float(request.POST.get("quoted-price-" + str(schedule.id)))
                            quoted_price = override_quoted_price
                        else:
                            if schedule.order.proposal.quote.estimate.estimatedetails.pre_demo > 0:
                                if schedule.pre_demo:
                                    quoted_price = estimate_predemo_calculator(schedule.order.proposal.quote.estimate.id)
                                    predemo_offset = float(schedule.order.predemo_offset)
                                    quoted_price = quoted_price - predemo_offset
                                else:
                                    pre_demo_price = estimate_predemo_calculator(schedule.order.proposal.quote.estimate.id)
                                    order_price = order_total_calculator(schedule.order.proposal.quote.estimate.id, schedule.order)
                                    final_offset = float(schedule.order.final_offset)
                                    quoted_price = order_price - pre_demo_price - final_offset
                            else:
                                quoted_price = float(order_total_calculator(schedule.order.proposal.quote.estimate.id, schedule.order))
                                offset = float(schedule.order.final_offset)
                                quoted_price = quoted_price - offset
                        settle_value = (float(this_settlement.contractor.profile.interest_percentage) / 100 * quoted_price) * schedule_tech.involvement_percentage / 100 * completion_percentage/100
                        total_settled_value = total_settled_value + round(settle_value, 2)
                        if prev_payment:
                            total_settled_value = (quoted_price - float(prev_payment)) * (float(this_settlement.contractor.profile.interest_percentage) / 100) * (schedule_tech.involvement_percentage / 100)
                        schedule_tech.settlement = True
                        schedule_tech.save()
                    else:
                        settled_type = False
                        schedule_tech = ScheduleTech.objects.get(schedule=schedule,
                                                                 assigned_to_contractor=this_settlement.contractor)
                        if request.POST.get("total-hour-" + str(schedule.id)):
                            override_total_duration = float(request.POST.get("total-hour-" + str(schedule.id)))
                            schedule_duration_in_hours = override_total_duration
                        else:
                            schedule_duration_in_hours = ((schedule.schedule_end - schedule.schedule_start).total_seconds()) / 3600
                        total_schedules_duration = total_schedules_duration + schedule_duration_in_hours
                        if schedule.order.proposal.quote.estimate.estimatedetails.pre_demo > 0:
                            if schedule.pre_demo:
                                quoted_price = estimate_predemo_calculator(schedule.order.proposal.quote.estimate.id)
                                predemo_offset = float(schedule.order.predemo_offset)
                                quoted_price = quoted_price - predemo_offset
                            else:
                                pre_demo_price = estimate_predemo_calculator(schedule.order.proposal.quote.estimate.id)
                                order_price = order_total_calculator(schedule.order.proposal.quote.estimate.id,
                                                                     schedule.order)
                                final_offset = float(schedule.order.final_offset)
                                quoted_price = order_price - pre_demo_price - final_offset
                        else:
                            quoted_price = float(order_total_calculator(schedule.order.proposal.quote.estimate.id, schedule.order))
                            offset = float(schedule.order.final_offset)
                            quoted_price = quoted_price - offset
                        settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(schedule_duration_in_hours)
                        total_settled_value = total_settled_value + round(settle_value, 2)
                        if prev_payment:
                            total_settled_value = (quoted_price - float(prev_payment)) * (float(this_settlement.contractor.profile.interest_percentage) / 100) * (schedule_tech.involvement_percentage / 100)
                        schedule_tech.settlement = True
                        schedule_tech.save()
                    if request.POST.get("settle-override-" + str(schedule.id)):
                        settled_schedule = SettledSchedule(settlement=this_settlement, schedule=schedule,
                                                           settled_total=quoted_price,
                                                           settled_value=total_settled_value,
                                                           settled_type=settled_type,
                                                           settled_hours=total_schedules_duration,
                                                           previous_payment=prev_payment,
                                                           settle_override=float(request.POST.get("settle-override-" + str(schedule.id))))
                    else:
                        settled_schedule = SettledSchedule(settlement=this_settlement, schedule=schedule,
                                                           settled_total=quoted_price,
                                                           settled_value=total_settled_value,
                                                           settled_type=settled_type,
                                                           settled_hours=total_schedules_duration,
                                                           previous_payment=prev_payment,
                                                           completion_percentage=completion_percentage)
                    settled_schedule.save()
            for maintenance in maintenances:
                total_settled_value = 0
                total_schedules_duration = 0
                if request.POST.get("maintenance-include-" + str(maintenance.id)):
                    if request.POST.get("maintenance-total-hour-" + str(maintenance.id)):
                        override_total_duration = float(request.POST.get("maintenance-total-hour-" + str(maintenance.id)))
                        schedule_duration_in_hours = override_total_duration
                    else:
                        schedule_duration_in_hours = ((maintenance.schedule_end - maintenance.schedule_start).total_seconds()) / 3600
                    total_schedules_duration = schedule_duration_in_hours
                    settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(schedule_duration_in_hours)
                    total_settled_value = total_settled_value + round(settle_value, 2)
                    maintenance.settlement = True
                    maintenance.save()
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
    schedules = SettledSchedule.objects.filter(settlement_id=settlement_id).order_by('schedule__schedule_start')
    maintenances = SettledMaintenances.objects.filter(settlement_id=settlement_id).order_by('maintenance___schedule_start')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('settlementHome')
        if request.POST.get("next"):
            for schedule in schedules:
                total_settled_value = 0
                total_schedules_duration = 0
                quoted_price = 0
                prev_payment = None
                completion_percentage = None
                if request.POST.get("pp-" + str(schedule.id)):
                    prev_payment = request.POST.get("pp-" + str(schedule.id))
                schedule_tech = ScheduleTech.objects.get(schedule=schedule.schedule,
                                                         assigned_to_contractor=this_settlement.contractor)
                if request.POST.get("or-toggle-" + str(schedule.id)):
                    settled_type = True
                    order_schedules = Schedule.objects.filter(order=schedule.schedule.order, pre_demo=schedule.schedule.pre_demo)
                    order_total_scheduled = 0
                    for order_schedule in order_schedules:
                        order_total_scheduled += ((order_schedule.schedule_end - order_schedule.schedule_start).total_seconds()) / 3600
                    schedule_duration_in_hours = ((schedule.schedule.schedule_end - schedule.schedule.schedule_start).total_seconds()) / 3600
                    total_schedules_duration = total_schedules_duration + schedule_duration_in_hours

                    completion_percentage = round(total_schedules_duration / order_total_scheduled * 100)
                    if schedule.schedule.pre_demo:
                        schedule.schedule.order.pre_demo_completion_percentage = 100
                    else:
                        schedule.schedule.order.completion_percentage = 100
                    schedule.schedule.order.save()
                    override_quoted_price = float(request.POST.get("quoted-price-" + str(schedule.id)))
                    quoted_price = override_quoted_price
                    settle_value = (float(this_settlement.contractor.profile.interest_percentage) / 100 * quoted_price) * schedule_tech.involvement_percentage / 100 * completion_percentage/100
                    total_settled_value = total_settled_value + round(settle_value, 2)
                    if prev_payment:
                        total_settled_value = (quoted_price - float(prev_payment)) * (
                                    float(this_settlement.contractor.profile.interest_percentage) / 100) * (
                                                          schedule_tech.involvement_percentage / 100)

                else:
                    settled_type = False
                    override_total_duration = float(request.POST.get("total-hour-" + str(schedule.id)))
                    total_schedules_duration = override_total_duration
                    schedule.settled_hours = total_schedules_duration
                    settle_value = float(this_settlement.contractor.profile.hourly_rate) * float(total_schedules_duration)
                    total_settled_value = total_settled_value + round(settle_value, 2)
                    if prev_payment:
                        total_settled_value = (quoted_price - float(prev_payment)) * (
                                    float(this_settlement.contractor.profile.interest_percentage) / 100) * (
                                                          schedule_tech.involvement_percentage / 100)

                schedule.settled_total = quoted_price
                schedule.settled_value = total_settled_value
                schedule.settled_type = settled_type
                schedule.previous_payment = prev_payment
                schedule.completion_percentage = completion_percentage
                settle_override = None
                if request.POST.get("settle-override-" + str(schedule.id)):
                    settle_override = float(request.POST.get("settle-override-" + str(schedule.id)))
                schedule.settle_override = settle_override
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
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  'STATIC_URL': settings.STATIC_URL,
                  'os': system(),
                  'settlement_id_prefix': settlement_id_prefix,
                  }

    return render(request, "settlementView.html", parameters)


@login_required
def generate_pdf(request, settlement_id):
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

    parameters = {'file_name': str(settlement.contractor.first_name) + ' ' + str(settlement.settlement_start.strftime("%B %Y")),
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
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  'STATIC_URL': settings.STATIC_URL,
                  'os': system(),
                  'settlement_id_prefix': settlement_id_prefix,
                  }
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/settlementTemplate.html', parameters,
                                                  'settlementPDF')

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as fh:
            my_file = fh.read()
            response = HttpResponse(my_file, content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + pdf_name
            response['Content-Length'] = len(my_file)
            return response
    else:
        return 'error'


@login_required
def settlement_delete(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            for settled_schedule in this_settlement.settledschedule_set.all():
                settled_schedule.schedule.order.fully_settled = False
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

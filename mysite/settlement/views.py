import datetime
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
from .forms import SettlementForm, SettledOrderForm
from .models import Settlement, SettledOrders, ModulesToEmailTemplateRelation
from ..core.forms import EmailForm
from ..core.views import htmlbodytemplate_tag_converter
from ..gi.views import order_total_calculator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, DEFAULT_FROM_EMAIL


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

    object_list = Settlement.objects.filter(Q(contractor__name__icontains=search)
                                            | Q(contractor__company__name__icontains=search)) \
        .order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    settlements = paginator.get_page(page)

    must_go = Settlement.objects.filter(settledorders__order__isnull=True)
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
    form = SettledOrderForm(request.POST or None, request.FILES or None, initial={'settlement': this_settlement.id})
    orders = Order.objects.filter(schedule__assigned_to_contractor=this_settlement.contractor).exclude(
        id__in=SettledOrders.objects.filter(Q(settlement__id=settlement_id) | Q(order__fully_settled=True)).values_list(
            'order_id')) \
        .order_by('-created_on')
    settled_orders = SettledOrders.objects.filter(settlement=this_settlement)
    settled_total = 0
    for settled_order in settled_orders:
        settled_total = settled_total + (
                settled_order.settled_value * settled_order.settlement.contractor.company.interest_percentage / 100)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            if not this_settlement.settledorders_set.exists():
                this_settlement.delete()
            return redirect('settlementHome')
        if request.POST.get("next"):
            return redirect('settlementView', this_settlement.id)
        if form.is_valid():
            if request.POST.get("add"):
                old_settled_value = Order.objects.get(id=form.cleaned_data['order'].id).order_settled_value
                new_settled_value = float(old_settled_value) + float(form.cleaned_data['settled_value'])
                Order.objects.filter(id=form.cleaned_data['order'].id).update(order_settled_value=new_settled_value)
                if float(new_settled_value) == float(
                        order_total_calculator(form.cleaned_data['order'].proposal.quote.estimate.id,
                                               form.cleaned_data['order'])):
                    Order.objects.filter(id=form.cleaned_data['order'].id).update(fully_settled=True)
                form.save()
                return redirect('settlementOrders', this_settlement.pk)
    parameters = {'form': form,
                  'this_settlement': this_settlement,
                  'orders': orders,
                  'settled_orders': settled_orders,
                  'settled_total': settled_total,
                  }
    return render(request, "settlementOrders.html", parameters)


@login_required
def settlement_view(request, settlement_id):
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_address = LicenseInfo.objects.get(key='OwnerAddress').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value
    settlement = Settlement.objects.get(id=settlement_id)
    settled_orders = SettledOrders.objects.filter(settlement=settlement)

    parameters = {'file_name': 'settlement-' + str(settlement_id),
                  'settlement': settlement,
                  'settled_orders': settled_orders,
                  'datetime': datetime.datetime.now(),
                  'license_owner': license_owner,
                  'owner_title': owner_title,
                  'owner_address': owner_address,
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
                  }
    settlement_pdf = Settlement.create_settlement_pdf(parameters)
    parameters['settlement_pdf'] = settlement_pdf[1]
    return render(request, "settlementView.html", parameters)


@login_required
def settlement_delete(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            for settled_order in this_settlement.settledorders_set.all():
                settled_order.order.fully_settled = False
                settled_order.order.order_settled_value = settled_order.order.order_settled_value - settled_order.settled_value
                settled_order.order.save()
            this_settlement.delete()
        return redirect('settlementHome')
    parameters = {'this_settlement': this_settlement
                  }
    return render(request, "settlementDelete.html", parameters)


@login_required
def settled_order_delete(request, settlement_id, settled_order_id):
    this_settled_order = get_object_or_404(SettledOrders, id=settled_order_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_settled_order.order.fully_settled = False
            this_settled_order.order.order_settled_value = this_settled_order.order.order_settled_value - this_settled_order.settled_value
            this_settled_order.order.save()
            this_settled_order.delete()
        return redirect('settlementOrders', settlement_id)
    parameters = {
        'this_settled_order': this_settled_order,
        'settlement_id': settlement_id,
    }
    return render(request, "settledOrderDelete.html", parameters)

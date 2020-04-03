from django.shortcuts import render, redirect, get_object_or_404
from .forms import SettlementForm, SettledOrderForm
from .models import Settlement, SettledOrders
import datetime
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from mysite.order.models import Order
from mysite.core.models import LicenseInfo, LicenseFiles


# Create your views here.

@login_required
def settlement_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Settlement.objects.all()

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    settlements = paginator.get_page(page)

    parameters = {'settlements': settlements,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
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
    orders = Order.objects.exclude(id__in=SettledOrders.objects.all().values_list('order_id')) \
        .order_by('-created_on')
    settled_orders = SettledOrders.objects.filter(settlement=this_settlement)
    settled_total = 0
    for settled_order in settled_orders:
        settled_total = settled_total + settled_order.settled_value
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('settlementHome')
        if form.is_valid():
            if request.POST.get("add"):
                form.save()
                return redirect('settlementOrders', this_settlement.pk)
            if request.POST.get("next"):
                return redirect('settlementView')
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
    estimate = Estimate.objects.get(id=estimate_id)
    instance = get_object_or_404(EstimateDetails, estimate=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate_id)
    estimate_sub = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        equipment_total = equipment_total_calculator(estimate_equipment_pricing)
        estimate_sub += equipment_total

    control_system_calculated = round(
        (estimate_sub * (1 + estimate.estimatedetails.control_system / 100)) - estimate_sub, 2)
    hours_calculated = round(
        (estimate_sub * (1 + estimate.estimatedetails.hours / 100)) - estimate_sub, 2)
    predemo_calculated = estimate.estimatedetails.pre_demo * 1200
    estimate_total = estimate_sub + control_system_calculated + hours_calculated \
                     + predemo_calculated \
                     + float(estimate.estimatedetails.adjustment)
    estimate_total = round(estimate_total, 2)
    estimate_work = estimate_total_work(estimate_id)
    estimate_work_in_hours = int(estimate_work / 60)
    estimate_work_in_minutes = int(estimate_work % 60)

    parameters = {'file_name': pdf_filename_generator(estimate.id, 'E'),
                  'estimate': estimate,
                  'estimate_equipments_pricing': estimate_equipments_pricing,
                  'estimate_sub': estimate_sub,
                  'estimate_total': estimate_total,
                  'estimate_work_in_hours': estimate_work_in_hours,
                  'estimate_work_in_minutes': estimate_work_in_minutes,
                  'control_system_calculated': control_system_calculated,
                  'hours_calculated': hours_calculated,
                  'predemo_calculated': predemo_calculated,
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
    estimate_pdf = Estimate.create_estimate_pdf(parameters)
    parameters['estimate_pdf'] = estimate_pdf[1]
    return render(request, "estimateBid.html", parameters)


@login_required
def settlement_delete(request, settlement_id):
    this_settlement = get_object_or_404(Settlement, id=settlement_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
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
            this_settled_order.delete()
        return redirect('settlementOrders', settlement_id)
    parameters = {
        'this_settled_order': this_settled_order,
        'settlement_id': settlement_id,
                  }
    return render(request, "settledOrderDelete.html", parameters)

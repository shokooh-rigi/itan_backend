from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, DEFAULT_FROM_EMAIL
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from ..core.forms import EmailForm
from django.contrib.auth.decorators import login_required
from platform import system


# Create your views here.


@login_required
def invoice_list(request):
    form = EmailForm(request.POST)
    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    if request.user.profile.cell == '' or request.user.profile.cell is None:
        user_cell = ''
    else:
        user_cell = request.user.profile.cell
    if request.user.profile.tel == '' or request.user.profile.tel is None:
        user_tel = LicenseInfo.objects.get(key='OwnerTel').value + ' Office'
    else:
        user_tel = request.user.profile.tel + ' Office'
    if request.method == 'POST':
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            to_email = to_email.replace(" ", "").split(',')
            cc = form.cleaned_data['cc']
            cc = cc.replace(" ", "").split(',')
            invoice_id = form.cleaned_data['invoice_id']
            subject = form.cleaned_data['subject']
            # subject = 'TAB Technologies INC. Invoice NO. ' + str(invoice_id).zfill(4)
            if ModulesToEmailTemplateRelation.objects.filter(module=3).exists():
                invoice_content = ModulesToEmailTemplateRelation.objects.get(module=4).template.content
            else:
                invoice_content = "There was no email template defined for 'Invoice'."
            if ModulesToEmailTemplateRelation.objects.filter(module=5).exists():
                footer_content = ModulesToEmailTemplateRelation.objects.get(module=5).template.content
            else:
                footer_content = "There was no email template defined for 'Email Footer'."
            footer_content = footer_content.__str__()\
                .replace("[user_name]", user_name)\
                .replace("[user_title]", user_title)\
                .replace("[user_cel]", user_cell)\
                .replace("[user_tel]", user_tel)
            message = invoice_content + '<br />' + footer_content
            try:
                msg = EmailMessage(
                    subject,
                    message,
                    DEFAULT_FROM_EMAIL,
                    [to_email],
                    cc=[cc],
                )
                msg.content_subtype = "html"
                msg.attach_file('media/pdfs/invoice/invoice-' + str(invoice_id) + '.pdf')
                msg.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('invoiceHome')

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

        object_list = Invoice.objects.filter(Q(order__proposal__quote__estimate__project__name__icontains=search)
                                              | Q(order__project_number__icontains=search)) \
            .filter(created_on__range=(from_date_obj, to_date_obj)).order_by(ordering)

    else:
        object_list = Invoice.objects.filter(Q(order__proposal__quote__estimate__project__name__icontains=search)
                                              | Q(order__project_number__icontains=search)) \
            .order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)

    parameters = {'invoices': invoices,
                  'form': form,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "invoice.html", parameters)


@login_required
def invoice_add(request):
    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    user_signature = request.user.profile.e_sign
    form = InvoiceForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    orders = Order.objects.filter(archive=False).exclude(id__in=Invoice.objects.all().values_list('order_id')).order_by('-created_on')
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('invoiceHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                invoice = form.save()
                total_amount_due = calculate_total_amount_due(invoice)
                parameters = {'form': form,
                              'file_name': 'invoice-' + str(invoice.order.project_number[3:]).zfill(3) + str(invoice.id).zfill(3),
                              'invoice': invoice,
                              'total_amount_due': total_amount_due,
                              'estimate': invoice.order.proposal.quote.estimate,
                              'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
                              'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
                              'owner_address': LicenseInfo.objects.get(key='OwnerAddress').value,
                              'owner_tel': LicenseInfo.objects.get(key='OwnerTel').value,
                              'owner_fax': LicenseInfo.objects.get(key='OwnerFax').value,
                              'owner_web': LicenseInfo.objects.get(key='OwnerWeb').value,
                              'owner_mail': LicenseInfo.objects.get(key='OwnerMail').value,
                              'owner_signature': LicenseFiles.objects.get(key='OwnerSignature').value,
                              'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
                              'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                              'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                              'company_name': LicenseInfo.objects.get(key='CompanyName').value,
                              'user_name': user_name,
                              'user_title': user_title,
                              'user_signature': user_signature,
                              'WEB_URL': WEB_URL,
                              'STATIC_URL': STATIC_URL,
                              'MEDIA_URL': MEDIA_URL,
                              'os': system(),
                              }
                invoice_pdf = Invoice.create_invoice_pdf(parameters)
                parameters['invoice_pdf'] = invoice_pdf[1]
                return redirect('invoiceView', invoice.id)
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "invoiceAdd.html", parameters)


@login_required
def invoice_view(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    total_amount_due = calculate_total_amount_due(invoice)
    parameters = {
        'invoice': invoice,
        'total_amount_due': total_amount_due,
        'estimate': invoice.order.proposal.quote.estimate,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
        'STATIC_URL': STATIC_URL,
    }
    return render(request, "invoiceView.html", parameters)


@login_required
def invoice_edit(request, invoice_id):
    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    user_signature = request.user.profile.e_sign
    this_invoice = get_object_or_404(Invoice, id=invoice_id)
    form = InvoiceForm(request.POST or None, request.FILES or None, instance=this_invoice)
    orders = Order.objects.filter(archive=False).exclude(id__in=Invoice.objects.all().values_list('order_id'))
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('invoiceHome')
        if form.is_valid():
            if request.POST.get("save"):
                invoice = form.save()
                total_amount_due = calculate_total_amount_due(invoice)
                parameters = {'form': form,
                              'file_name': 'invoice-' + str(invoice.order.project_number[3:]).zfill(3) + str(invoice.id).zfill(3),
                              'invoice': invoice,
                              'total_amount_due': total_amount_due,
                              'estimate': invoice.order.proposal.quote.estimate,
                              'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
                              'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
                              'owner_address': LicenseInfo.objects.get(key='OwnerAddress').value,
                              'owner_tel': LicenseInfo.objects.get(key='OwnerTel').value,
                              'owner_fax': LicenseInfo.objects.get(key='OwnerFax').value,
                              'owner_web': LicenseInfo.objects.get(key='OwnerWeb').value,
                              'owner_mail': LicenseInfo.objects.get(key='OwnerMail').value,
                              'owner_signature': LicenseFiles.objects.get(key='OwnerSignature').value,
                              'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
                              'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                              'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                              'company_name': LicenseInfo.objects.get(key='CompanyName').value,
                              'user_name': user_name,
                              'user_title': user_title,
                              'user_signature': user_signature,
                              'WEB_URL': WEB_URL,
                              'STATIC_URL': STATIC_URL,
                              'MEDIA_URL': MEDIA_URL,
                              'os': system(),
                              }
                Invoice.delete_invoice_pdf(parameters)
                invoice_pdf = Invoice.create_invoice_pdf(parameters)
                parameters['invoice_pdf'] = invoice_pdf[1]
                return redirect('invoiceHome')
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "invoiceEdit.html", parameters)


@login_required
def invoice_delete(request, invoice_id):
    this_invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST" and request.user.is_authenticated and this_invoice.order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            parameters = {'file_name': 'invoice-' + str(this_invoice.order.project_number[3:]).zfill(3) + str(this_invoice.id).zfill(3),
                          }
            Invoice.delete_invoice_pdf(parameters)
            this_invoice.delete()
        return redirect('invoiceHome')
    elif request.method == "POST" and request.user.is_authenticated and this_invoice.order.proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_invoice': this_invoice,
                'error_msg': error_msg
            }
            return render(request, "invoiceDelete.html", parameters)
        return redirect('invoiceHome')
    parameters = {'this_invoice': this_invoice
                  }
    return render(request, "invoiceDelete.html", parameters)


@login_required
def invoice_archive(request, invoice_id):
    this_invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST" and request.user.is_authenticated and this_invoice.order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_invoice.archive = True
            this_invoice.save()
        return redirect('invoiceHome')
    elif request.method == "POST" and request.user.is_authenticated and this_invoice.order.proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_invoice': this_invoice,
                'error_msg': error_msg
            }
            return render(request, "invoiceArchive.html", parameters)
        return redirect('invoiceHome')
    parameters = {'this_invoice': this_invoice
                  }
    return render(request, "invoiceArchive.html", parameters)


def equipment_total_calculator(equipment):
    if equipment.price_override:
        return float(equipment.price_override) * float(equipment.quantity)
    else:
        return float(equipment.equipment.price) * float(equipment.quantity)


def estimate_total_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate_id)
    estimate_sub = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        equipment_total = equipment_total_calculator(estimate_equipment_pricing)
        estimate_sub += float(equipment_total)

    control_system_calculated = round(
        (estimate_sub * (1 + estimate.estimatedetails.control_system / 100)) - estimate_sub, 2)
    hours_calculated = round(
        (estimate_sub * (1 + estimate.estimatedetails.hours / 100)) - estimate_sub, 2)
    predemo_calculated = estimate.estimatedetails.pre_demo * 1200
    estimate_total = estimate_sub + control_system_calculated + hours_calculated + predemo_calculated \
                     + float(estimate.estimatedetails.adjustment)
    estimate_total = round(estimate_total, 2)
    return estimate_total


def order_total_calculator(estimate_id, order):
    estimate_total = estimate_total_calculator(estimate_id)
    change_orders = ChangeOrder.objects.filter(order=order)
    co_total = 0
    for change_order in change_orders:
        co_total = co_total + change_order.amount
    order_total = estimate_total + float(co_total)
    order_total = round(order_total, 2)
    return order_total


def calculate_total_amount_due(invoice):
    sub_total = order_total_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
    completed_percentage = invoice.percent_of_performance_completed
    received_to_date = float(invoice.total_payment_received_to_date)
    past_amount = float(invoice.past_due_amount)
    total = (sub_total * completed_percentage / 100)
    total = total - received_to_date + past_amount
    return total

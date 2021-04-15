import math
import os
import re
from itertools import chain
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from ..estimator.views import estimate_total_calculator
from ..gi.models import *
from mysite.gi.views import calculate_total_amount_due, calculate_remaining_invoice_due, calculate_total_paid
from django.utils.dateparse import parse_date


# Create your views here.


def is_num(data):
    try:
        int(data)
        return True
    except ValueError:
        return False


@login_required
def customer_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-customer_id'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    if ordering.startswith('-'):
        if is_num(search):
            object_list = ContactInfo.objects.filter(Q(name__icontains=search) | Q(customer_id=search)).order_by(F(ordering[1:]).asc(nulls_last=True))
        else:
            object_list = ContactInfo.objects.filter(name__icontains=search).order_by(F(ordering[1:]).asc(nulls_last=True))
    else:
        if is_num(search):
            object_list = ContactInfo.objects.filter(Q(name__icontains=search) | Q(customer_id=search)).order_by(F(ordering).desc(nulls_last=True))
        else:
            object_list = ContactInfo.objects.filter(name__icontains=search).order_by(F(ordering).desc(nulls_last=True))

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    customers = paginator.get_page(page)

    parameters = {'customers': customers,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "customerList.html", parameters)


@login_required
def mass_payment(request, contact_id):
    customer = ContactInfo.objects.get(id=contact_id)
    invoices = Invoice.objects.filter(order__proposal__quote__estimate__customer__company__id=contact_id)
    total_invoiced = 0
    total_paid = 0
    total_balance_due = 0
    for invoice in invoices:
        if calculate_remaining_invoice_due(invoice) == 0:
            invoices = invoices.exclude(id=invoice.id)
        else:
            total_invoiced += calculate_total_amount_due(invoice)
            total_paid += calculate_total_paid(invoice)
            total_balance_due += calculate_remaining_invoice_due(invoice)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('customerListHome')
        if request.POST.get("next"):
            payment_no = request.POST.get("payment-number")
            payment_date = request.POST.get("payment-date")
            payment_date = datetime.datetime.strptime(payment_date, "%m/%d/%Y").date()
            payment_desc = request.POST.get("payment-desc")
            for invoice in invoices:
                paid_amount = request.POST.get("amount-" + str(invoice.id))
                if paid_amount and paid_amount != 0:
                    new_payment = InvoiceTransaction(invoice=invoice, amount=paid_amount, payment_date=payment_date, payment_no=payment_no, created_by=request.user)
                    new_payment.save()
                    if request.user.last_name == '' or request.user.last_name is None:
                        user_name = 'TAB Technologies, INC. Operator'
                    else:
                        user_name = request.user.first_name + " " + request.user.last_name
                    if request.user.profile.title == '' or request.user.profile.title is None:
                        user_title = 'Estimator'
                    else:
                        user_title = request.user.profile.title
                    user_signature = request.user.profile.e_sign
                    change_orders = ChangeOrder.objects.filter(order=invoice.order)
                    total_amount_due = calculate_total_amount_due(invoice)
                    transactions_count = InvoiceTransaction.objects.filter(invoice=invoice.id).count()
                    change_orders_count = ChangeOrder.objects.filter(order=invoice.order).count()
                    total_count = transactions_count + change_orders_count + invoice.times_estimate_changed
                    new_file_name = 'Invoice-' + str(invoice.order.project_number[3:]).zfill(3) + '-' + str(
                        invoice.id).zfill(3) + '-' + str(total_count).zfill(3)
                    parameters = {
                        'file_name': new_file_name,
                        'total_count': total_count,
                        'invoice': invoice,
                        'change_orders': change_orders,
                        'total_amount_due': total_amount_due,
                        'estimate': invoice.order.proposal.quote.estimate,
                        'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
                        'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
                        'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
                        'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
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
                    Invoice.create_invoice_pdf(parameters)
                    total_invoiced = calculate_total_amount_due(invoice)
                    total_paid = calculate_total_paid(invoice)
                    balance_due = calculate_remaining_invoice_due(invoice)
                    new_history = InvoiceHistory(invoice=invoice, total_invoiced=total_invoiced, total_paid=total_paid, balance_due=balance_due, pdf_filename=new_file_name)
                    new_history.save()
            return redirect('customerListHome')

    parameters = {
        'customer': customer,
        'invoices': invoices,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'total_balance_due': total_balance_due,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "massPayment.html", parameters)

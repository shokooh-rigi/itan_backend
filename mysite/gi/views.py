from platform import system
import os
from django.contrib.auth.decorators import login_required
from django.core.mail import BadHeaderError, EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from ..core.forms import EmailForm
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, DEFAULT_FROM_EMAIL
from django import forms
from ..projectprocess.models import ProjectProcess
from ..order.templatetags.order_tags import *
import requests
import os
from ..s3_file_manager import *

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
            invoice_id = form.cleaned_data['email_id']
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
            footer_content = footer_content.__str__() \
                .replace("[user_name]", user_name) \
                .replace("[user_title]", user_title) \
                .replace("[user_cel]", user_cell) \
                .replace("[user_tel]", user_tel)
            message = invoice_content + '<br />' + footer_content
            try:
                msg = EmailMessage(
                    subject,
                    message,
                    DEFAULT_FROM_EMAIL,
                    to_email,
                    cc=cc,
                )
                msg.content_subtype = "html"
                latest_invoice_history = InvoiceHistory.objects.filter(invoice__id=invoice_id).order_by('id').last()
                s3 = S3()
                response = requests.get(s3.get_bucket_object('media/pdfs/invoice/' + latest_invoice_history.pdf_filename + '.pdf'))
                f = open('media/pdfs/invoice/' + latest_invoice_history.pdf_filename + '.pdf', 'wb')
                f.write(response.content)
                f.close()
                msg.attach_file('media/pdfs/invoice/' + latest_invoice_history.pdf_filename + '.pdf')
                msg.send()
                os.remove('media/pdfs/invoice/' + latest_invoice_history.pdf_filename + '.pdf')
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

    if request.GET.get('type') == 'fully-paid':
        to_be_deleted = []
        for invoice in object_list:
            if calculate_remaining_invoice_due(invoice) == 0:
                to_be_deleted.append(invoice.id)
        object_list = object_list.filter(id__in=to_be_deleted).distinct()
    if request.GET.get('type') == 'partial-paid':
        to_be_deleted = []
        for invoice in object_list:
            if calculate_remaining_invoice_due(invoice) != 0:
                to_be_deleted.append(invoice.id)
        object_list = object_list.filter(id__in=to_be_deleted).filter(invoicetransaction__isnull=False).distinct()
    if request.GET.get('type') == 'not-paid':
        object_list = object_list.filter(invoicetransaction__isnull=True)

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
def invoice_add(request, order_id=None):
    form = InvoiceForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if order_id:
        orders = Order.objects.filter(id=order_id)
    else:
        orders = Order.objects.filter(archive=False).exclude(id__in=Invoice.objects.all().values_list('order_id')).order_by('-created_on')
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('invoiceHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user

                invoice = form.save()
                if invoice.order.proposal.quote.estimate.estimatedetails.pre_demo > 0:
                    if request.POST.get("predemo_selected") and request.POST.get("final_selected"):
                        invoice_type = 1
                    elif request.POST.get("predemo_selected"):
                        invoice_type = 2
                    else:
                        invoice_type = 3
                    invoice.invoice_type = invoice_type
                    invoice.save()
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
                parameters = {
                    'file_name': 'Invoice-' + str(invoice.order.project_number[3:]).zfill(3) + '-' + str(
                        invoice.id).zfill(3) + '-1',
                    'total_count': '1',
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
                    'invoice_view_page': True,
                }
                invoice_pdf = Invoice.create_invoice_pdf(parameters)
                parameters['invoice_pdf'] = invoice_pdf[1]
                total_invoiced = calculate_total_amount_due(invoice)
                total_paid = calculate_total_paid(invoice)
                balance_due = calculate_remaining_invoice_due(invoice)
                new_object = InvoiceHistory(invoice=invoice, total_invoiced=total_invoiced, total_paid=total_paid,
                                            balance_due=balance_due
                                            , pdf_filename='Invoice-' + str(invoice.order.project_number[3:]).zfill(
                        3) + '-' + str(invoice.id).zfill(3) + '-1')
                new_object.save()

                if ProjectProcess.objects.filter(order_id=invoice.order.id).exists():
                    project_process = get_object_or_404(ProjectProcess, order_id=invoice.order.id)
                else:
                    project_process = ProjectProcess(order=invoice.order)
                project_process.tech_package = True
                project_process.tech_scheduled = True
                project_process.job_completed = True
                project_process.report_out = True
                project_process.invoiced_date = datetime.datetime.now().date()
                project_process.invoiced = True
                project_process.save()
                return redirect('invoiceHome')
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "invoiceAdd.html", parameters)


@login_required
def invoice_edit(request, invoice_id):
    this_invoice = get_object_or_404(Invoice, id=invoice_id)
    form = InvoiceForm(request.POST or None, request.FILES or None, instance=this_invoice)
    orders = Order.objects.filter(archive=False).exclude(id__in=Invoice.objects.all().values_list('order_id'))
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('invoiceHome')
        if form.is_valid():
            if request.POST.get("save"):
                invoice = form.save()
                if invoice.order.proposal.quote.estimate.estimatedetails.pre_demo > 0:
                    if request.POST.get("predemo_selected") and request.POST.get("final_selected"):
                        invoice_type = 1
                    elif request.POST.get("predemo_selected"):
                        invoice_type = 2
                    else:
                        invoice_type = 3
                    invoice.invoice_type = invoice_type
                    invoice.save()
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
                total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1
                new_file_name = 'Invoice-' + str(invoice.order.project_number[3:]).zfill(3) + '-' + str(
                        invoice.id).zfill(3) + '-' + str(total_count)
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
                new_object = InvoiceHistory(invoice=invoice, total_invoiced=total_invoiced, total_paid=total_paid, balance_due=balance_due, pdf_filename=new_file_name)
                new_object.save()
                return redirect('invoiceHome')
    parameters = {
        'form': form,
        'orders': orders,
        'invoice': this_invoice
    }
    return render(request, "invoiceEdit.html", parameters)


@login_required
def invoice_view(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    latest_invoice_history = InvoiceHistory.objects.filter(invoice=invoice).order_by('id').last()
    num_results = InvoiceHistory.objects.filter(invoice=invoice).count()
    if num_results == 0:
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
        parameters = {
            'file_name': 'Invoice-' + str(invoice.order.project_number[3:]).zfill(3) + '-' + str(
                invoice.id).zfill(3) + '-1',
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
            'invoice_view_page': True,
        }
        invoice_pdf = Invoice.create_invoice_pdf(parameters)
        parameters['invoice_pdf'] = invoice_pdf[1]
        total_invoiced = calculate_total_amount_due(invoice)
        total_paid = calculate_total_paid(invoice)
        balance_due = calculate_remaining_invoice_due(invoice)
        new_object = InvoiceHistory(invoice=invoice, total_invoiced=total_invoiced, total_paid=total_paid, balance_due=balance_due
                                    , pdf_filename='Invoice-' + str(invoice.order.project_number[3:]).zfill(3) + '-' + str(invoice.id).zfill(3) + '-1')
        new_object.save()
    parameters = {
        'latest_invoice_history': latest_invoice_history,
        'invoice': invoice,
        'estimate': invoice.order.proposal.quote.estimate,
        'WEB_URL': WEB_URL,
        'STATIC_URL': STATIC_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "invoiceView.html", parameters)


@login_required
def invoice_delete(request, invoice_id):
    this_invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST" and request.user.is_authenticated and this_invoice.created_by == request.user:
        if request.POST.get("confirm"):
            parameters = {'file_name': 'invoice-' + str(this_invoice.order.project_number[3:]).zfill(3) + str(
                this_invoice.id).zfill(3),
                          }
            Invoice.delete_invoice_pdf(parameters)
            try:
                this_invoice.order.projectprocess.invoiced = False
                this_invoice.order.projectprocess.invoiced_date = None
                this_invoice.order.projectprocess.save()
            except:
                pass
            this_invoice.delete()
        return redirect('invoiceHome')
    elif request.method == "POST" and request.user.is_authenticated and this_invoice.created_by != request.user:
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
    if request.method == "POST" and request.user.is_authenticated and this_invoice.created_by == request.user:
        if request.POST.get("confirm"):
            this_invoice.archive = True
            this_invoice.save()
        return redirect('invoiceHome')
    elif request.method == "POST" and request.user.is_authenticated and this_invoice.created_by != request.user:
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


@login_required
def invoice_payment(request, invoice_id):
    nowww = datetime.datetime.now().strftime("%m/%d/%Y")
    form = InvoicePaymentForm(request.POST or None, request.FILES or None, initial={'created_by': request.user, 'invoice': invoice_id})
    invoice = Invoice.objects.get(id=invoice_id)
    invoice_transactions = InvoiceTransaction.objects.filter(invoice=invoice_id)
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('invoiceHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                form.cleaned_data['invoice'] = invoice_id
                transaction = form.save()
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
                transactions_count = InvoiceTransaction.objects.filter(invoice=invoice_id).count()
                change_orders_count = ChangeOrder.objects.filter(order=invoice.order).count()
                total_count = InvoiceHistory.objects.filter(invoice=invoice).count() + 1
                new_file_name = 'Invoice-' + str(invoice.order.project_number[3:]).zfill(3) + '-' + str(
                        invoice.id).zfill(3) + '-' + str(total_count)
                parameters = {
                    'nowww': nowww,
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
                new_object = InvoiceHistory(invoice=invoice, total_invoiced=total_invoiced, total_paid=total_paid, balance_due=balance_due, pdf_filename=new_file_name)
                new_object.save()
                return redirect('invoicePayment', invoice_id)
    parameters = {'form': form,
                  'invoice_transactions': invoice_transactions,
                  'invoice': invoice
                  }
    return render(request, "invoicePayment.html", parameters)


@login_required
def invoice_payment_delete(request, transaction_id):
    this_transaction = get_object_or_404(InvoiceTransaction, id=transaction_id)
    invoice_id = this_transaction.invoice.id
    if request.method == "POST" and request.user.is_authenticated and this_transaction.created_by == request.user:
        if request.POST.get("confirm"):
            total_invoiced = calculate_total_amount_due(this_transaction.invoice)
            total_paid = calculate_total_paid(this_transaction.invoice)
            balance_due = calculate_remaining_invoice_due(this_transaction.invoice)
            try:
                this_invoice_history = get_object_or_404(InvoiceHistory,
                                                         invoice=this_transaction.invoice,
                                                         total_invoiced=total_invoiced,
                                                         total_paid=total_paid,
                                                         balance_due=balance_due)
                this_invoice_history.delete()
            except:
                pass
            this_transaction.delete()
        return redirect('invoicePayment', invoice_id)
    elif request.method == "POST" and request.user.is_authenticated and this_transaction.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_transaction': this_transaction,
                'invoice_id': invoice_id,
                'error_msg': error_msg
            }
            return render(request, "transactionDelete.html", parameters)
        return redirect('invoicePayment', invoice_id)
    parameters = {'this_transaction': this_transaction,
                  'invoice_id': invoice_id
                  }
    return render(request, "transactionDelete.html", parameters)


@login_required
def invoice_history(request, invoice_id):
    invoice_histories = InvoiceHistory.objects.filter(invoice__id=invoice_id)
    invoice = Invoice.objects.get(id=invoice_id)
    parameters = {
        'invoice_histories': invoice_histories,
        'invoice': invoice,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "invoiceHistory.html", parameters)


@login_required
def account_summary_list(request):
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
            email_id = form.cleaned_data['email_id']
            subject = form.cleaned_data['subject']
            if ModulesToEmailTemplateRelation.objects.filter(module=9).exists():
                invoice_content = ModulesToEmailTemplateRelation.objects.get(module=9).template.content
            else:
                invoice_content = "There was no email template defined for 'Account Summary'."
            if ModulesToEmailTemplateRelation.objects.filter(module=5).exists():
                footer_content = ModulesToEmailTemplateRelation.objects.get(module=5).template.content
            else:
                footer_content = "There was no email template defined for 'Email Footer'."
            footer_content = footer_content.__str__() \
                .replace("[user_name]", user_name) \
                .replace("[user_title]", user_title) \
                .replace("[user_cel]", user_cell) \
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
                msg.attach_file('media/pdfs/accountsummary/AccountSummary-' + str(email_id) + '.pdf')
                msg.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('accountSummaryHome')

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

        object_list = AccountSummary.objects.filter(created_on__range=(from_date_obj, to_date_obj)).order_by(ordering)

    else:
        object_list = AccountSummary.objects.order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    account_summaries = paginator.get_page(page)

    parameters = {'account_summaries': account_summaries,
                  'form': form,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "accountSummary.html", parameters)



@login_required
def account_summary_add(request, customer_id=None):
    form = AccountSummaryForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if customer_id:
        customers = ContactInfo.objects.filter(id=customer_id)
    else:
        customers = ContactInfo.objects.filter(company_type__name__iexact='mechanical contractor')
    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    user_signature = request.user.profile.e_sign
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('accountSummaryHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                customer = form.cleaned_data['customer']
                customer_invoices = Invoice.objects.filter(order__proposal__quote__estimate__customer__company=customer).order_by('created_on')
                this_total = 0
                for invoice in customer_invoices:
                    this_total += float(calculate_remaining_invoice_due(invoice))
                    if calculate_remaining_invoice_due(invoice) == 0:
                        customer_invoices = customer_invoices.exclude(pk=invoice.pk)
                if this_total == 0:
                    error_msg = "This Customer has no remained invoice to pay."
                    parameters = {
                        'error_msg': error_msg,
                        'form': form,
                        'customers': customers
                    }
                    return render(request, "accountSummaryAdd.html", parameters)
                account_summary = form.save()
                account_summary.total = float(this_total)
                account_summary.save()
                parameters = {'form': form,
                              'account_summary': account_summary,
                              'customer_invoices': customer_invoices,
                              'file_name': 'AccountSummary-' + account_summary.statement_no,
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
                account_summary_pdf = AccountSummary.create_account_summary_pdf(parameters)
                parameters['account_summary_pdf'] = account_summary_pdf[1]
                return redirect('accountSummaryHome')
    parameters = {'form': form,
                  'customers': customers
                  }
    return render(request, "accountSummaryAdd.html", parameters)


@login_required
def accout_summary_delete(request, account_summary_id):
    this_account_summary = get_object_or_404(AccountSummary, id=account_summary_id)
    if request.method == "POST" and request.user.is_authenticated and this_account_summary.created_by == request.user:
        if request.POST.get("confirm"):
            parameters = {'file_name': 'AccountSummary-' + this_account_summary.statement_no,
                          }
            AccountSummary.delete_account_summary_pdf(parameters)
            this_account_summary.delete()
        return redirect('accountSummaryHome')
    elif request.method == "POST" and request.user.is_authenticated and this_account_summary.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_account_summary': this_account_summary,
                'error_msg': error_msg
            }
            return render(request, "accountSummaryDelete.html", parameters)
        return redirect('invoicePayment')
    parameters = {'this_account_summary': this_account_summary,
                  }
    return render(request, "accountSummaryDelete.html", parameters)

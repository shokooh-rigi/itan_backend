import json
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.mail import BadHeaderError, EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from ..gi.models import *
from ..core.forms import EmailForm
from ..core.views import htmlbodytemplate_tag_converter
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, DEFAULT_FROM_EMAIL
from ..gi.views import calculate_total_amount_due, calculate_total_paid, calculate_remaining_invoice_due
from .templatetags.estimator_tags import *
from django.db.models import Count
import requests
import os
from copy import deepcopy

# Create your views here.


@login_required
def estimate_list(request):
    form = EmailForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            to_email = to_email.replace(" ", "").replace(";", ",").split(',')
            cc = form.cleaned_data['cc']
            cc = cc.replace(" ", "").replace(";", ",").split(',')
            email_id = form.cleaned_data['email_id']
            subject = form.cleaned_data['subject']
            this_estimate = get_object_or_404(Estimate, id=email_id)
            customer = this_estimate.customer
            if ModulesToEmailTemplateRelation.objects.filter(module=1).exists():
                body_content = get_object_or_404(ModulesToEmailTemplateRelation, module=1).template.content
            else:
                body_content = "There was no email template defined for 'Estimate'."
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
                s3 = S3()
                response = requests.get(s3.get_bucket_object('media/pdfs/estimate/' + pdf_filename_generator(email_id, 'E') + '.pdf'))
                f = open('media/pdfs/estimate/' + pdf_filename_generator(email_id, 'E') + '.pdf', 'wb')
                f.write(response.content)
                f.close()
                msg.attach_file('media/pdfs/estimate/' + pdf_filename_generator(email_id, 'E') + '.pdf')
                msg.send()
                os.remove('media/pdfs/estimate/' + pdf_filename_generator(email_id, 'E') + '.pdf')
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('estimatorHome')

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

        object_list = Estimate.objects.filter(Q(project__name__icontains=search)
                                              | Q(customer__company__name__icontains=search)) \
            .filter(due_date__range=(from_date_obj, to_date_obj)).filter(archive=False)

    else:
        object_list = Estimate.objects.filter(Q(project__name__icontains=search)
                                              | Q(customer__company__name__icontains=search)) \
            .filter(archive=False)

    object_list = object_list.annotate(null_count=Count('quote')).order_by('null_count', ordering)

    total_rows = object_list.count()

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    estimates = paginator.get_page(page)

    parameters = {'estimates': estimates,
                  'form': form,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'total_rows': total_rows,
                  }
    return render(request, "estimator.html", parameters)


@login_required
def quotation_list(request):
    form = EmailForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            to_email = to_email.replace(" ", "").replace(";", ",").split(',')
            cc = form.cleaned_data['cc']
            cc = cc.replace(" ", "").replace(";", ",").split(',')
            cc.append('est@tabtechinc.com')
            cc.append('a.behehsti@tabtechinc.com')
            email_id = form.cleaned_data['email_id']
            subject = form.cleaned_data['subject']
            this_estimate = get_object_or_404(Estimate, id=email_id)
            customer = this_estimate.customer
            if ModulesToEmailTemplateRelation.objects.filter(module=2).exists():
                body_content = get_object_or_404(ModulesToEmailTemplateRelation, module=2).template.content
            else:
                body_content = "There was no email template defined for 'Quotation'."
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
                s3 = S3()
                response = requests.get(s3.get_bucket_object('media/pdfs/quote/' + pdf_filename_generator(email_id, 'Q') + '.pdf'))
                f = open('media/pdfs/quote/' + pdf_filename_generator(email_id, 'Q') + '.pdf', 'wb')
                f.write(response.content)
                f.close()
                msg.attach_file('media/pdfs/quote/' + pdf_filename_generator(email_id, 'Q') + '.pdf')
                msg.send()
                os.remove('media/pdfs/quote/' + pdf_filename_generator(email_id, 'Q') + '.pdf')
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('quotationHome')

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

        object_list = Quote.objects.filter(Q(estimate__project__name__icontains=search)
                                           | Q(estimate__customer__company__name__icontains=search)) \
            .filter(estimate__due_date__range=(from_date_obj, to_date_obj)).filter(archive=False).order_by(ordering)

    else:
        object_list = Quote.objects.filter(Q(estimate__project__name__icontains=search)
                                           | Q(estimate__customer__company__name__icontains=search)) \
            .filter(archive=False).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    quotes = paginator.get_page(page)

    parameters = {'quotes': quotes,
                  'form': form,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "quotation.html", parameters)


@login_required
def proposal_list(request):
    form = EmailForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            to_email = to_email.replace(" ", "").replace(";", ",").split(',')
            cc = form.cleaned_data['cc']
            cc = cc.replace(" ", "").replace(";", ",").split(',')
            cc.append('est@tabtechinc.com')
            cc.append('a.behehsti@tabtechinc.com')
            email_id = form.cleaned_data['email_id']
            subject = form.cleaned_data['subject']
            this_estimate = get_object_or_404(Estimate, id=email_id)
            customer = this_estimate.customer
            if ModulesToEmailTemplateRelation.objects.filter(module=3).exists():
                body_content = get_object_or_404(ModulesToEmailTemplateRelation, module=3).template.content
            else:
                body_content = "There was no email template defined for 'Proposal'."
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
                s3 = S3()
                response = requests.get(s3.get_bucket_object('media/pdfs/proposal/' + pdf_filename_generator(email_id, 'P') + '.pdf'))
                f = open('media/pdfs/proposal/' + pdf_filename_generator(email_id, 'P') + '.pdf', 'wb')
                f.write(response.content)
                f.close()
                msg.attach_file('media/pdfs/proposal/' + pdf_filename_generator(email_id, 'P') + '.pdf')
                msg.send()
                os.remove('media/pdfs/proposal/' + pdf_filename_generator(email_id, 'P') + '.pdf')
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('proposalHome')
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

        object_list = Proposal.objects.filter(Q(quote__estimate__project__name__icontains=search)
                                              | Q(quote__estimate__customer__company__name__icontains=search)) \
            .filter(quote__estimate__due_date__range=(from_date_obj, to_date_obj)).filter(archive=False).order_by(
            ordering)

    else:
        object_list = Proposal.objects.filter(Q(quote__estimate__project__name__icontains=search)
                                              | Q(quote__estimate__customer__company__name__icontains=search)) \
            .filter(archive=False).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    proposals = paginator.get_page(page)
    parameters = {'proposals': proposals,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'form': form,
                  }
    return render(request, "proposal.html", parameters)


@login_required
def estimator_add(request, bfm_id=None):
    if bfm_id:
        form = EstimateFullForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
        bfms = BidFile.objects.filter(id=bfm_id)
    else:
        form = EstimateForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
        bfms = BidFile.objects.filter(archive=False).exclude(id__in=Estimate.objects.filter(bfm_id__isnull=False).values_list('bfm_id')).order_by('due_date')
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('estimatorHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                new_estimate = form.save()
                EstimateDetails.objects.filter(estimate=new_estimate) \
                    .update(pre_demo=form.cleaned_data['predemo'])
                return HttpResponseRedirect(reverse('estimateEquipment', args=(new_estimate.pk, 0)))
    parameters = {
        'form': form,
        'bfms': bfms,
        'page_action': 'New',
    }
    return render(request, "estimatorAdd.html", parameters)


@login_required
def estimator_edit(request, estimate_id):
    this_estimate = get_object_or_404(Estimate, id=estimate_id)
    form = EstimateForm(request.POST or None, instance=this_estimate)
    no_bfm = 1
    if this_estimate.bfm:
        bfms = BidFile.objects.filter(id=this_estimate.bfm.id)
        no_bfm = 0
    else:
        bfms = None

    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('estimatorHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                new_estimate = form.save()
                EstimateDetails.objects.filter(estimate=new_estimate) \
                    .update(pre_demo=form.cleaned_data['predemo'])
                estimate_equipments = EstimateEquipment.objects.filter(estimate=new_estimate)
                for this_equipment in estimate_equipments:
                    if this_equipment.equipment.service not in new_estimate.service.all():
                        this_equipment.flag = False
                        this_equipment.save()
                    else:
                        this_equipment.flag = True
                        this_equipment.save()
                return HttpResponseRedirect(reverse('estimateEquipment', args=(new_estimate.pk, 0)))
    parameters = {
        'form': form,
        'bfms': bfms,
        'no_bfm': no_bfm,
        'page_action': 'Edit',
    }
    return render(request, "estimatorEdit.html", parameters)


@login_required
def quote_add(request, estimate_id=None):
    form = QuoteForm(request.POST or None, request.FILES or None)
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_address_line1 = LicenseInfo.objects.get(key='OwnerAddressLine1').value
    owner_address_line2 = LicenseInfo.objects.get(key='OwnerAddressLine2').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    user_signature = request.user.profile.e_sign
    if request.user.profile.cell == '' or request.user.profile.cell is None:
        user_cell = ''
    else:
        user_cell = request.user.profile.cell
    if estimate_id:
        estimates = Estimate.objects.filter(id=estimate_id)
    else:
        estimates = Estimate.objects.filter(archive=False).exclude(id__in=Quote.objects.all().values_list('estimate_id')).order_by('-created_on')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('quotationHome')
        if form.is_valid():
            if request.POST.get("next"):
                quote = form.save()
                if quote.estimate.bfm:
                    this_bfm = get_object_or_404(BidFile, id=quote.estimate.bfm_id)
                    this_bfm.archive = True
                    this_bfm.save()
                predemo_calculated = quote.estimate.estimatedetails.pre_demo * 1200
                parameters = {'form': form,
                              'file_name': pdf_filename_generator(quote.estimate.id, 'Q'),
                              'quote': quote,
                              'predemo_calculated': predemo_calculated,
                              'license_owner': license_owner,
                              'owner_title': owner_title,
                              'owner_address_line1': owner_address_line1,
                              'owner_address_line2': owner_address_line2,
                              'owner_tel': owner_tel,
                              'owner_fax': owner_fax,
                              'owner_web': owner_web,
                              'owner_mail': owner_mail,
                              'owner_signature': owner_signature,
                              'owner_logo': owner_logo,
                              'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                              'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                              'company_name': company_name,
                              'user_name': user_name,
                              'user_title': user_title,
                              'user_signature': user_signature,
                              'user_cell': user_cell,
                              'WEB_URL': WEB_URL,
                              'STATIC_URL': STATIC_URL,
                              'MEDIA_URL': MEDIA_URL,
                              'os': system(),
                              }
                quote_pdf = Quote.create_quote_pdf(parameters)
                parameters['quote_pdf'] = quote_pdf[1]
                return redirect('quotationHome')
    parameters = {'form': form,
                  'estimates': estimates
                  }
    return render(request, "quoteAdd.html", parameters)


@login_required
def proposal_add(request, quote_id=None):
    form = ProposalForm(request.POST or None, request.FILES or None)
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_address_line1 = LicenseInfo.objects.get(key='OwnerAddressLine1').value
    owner_address_line2 = LicenseInfo.objects.get(key='OwnerAddressLine2').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value
    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    user_signature = request.user.profile.e_sign
    if request.user.profile.cell == '' or request.user.profile.cell is None:
        user_cell = ''
    else:
        user_cell = request.user.profile.cell
    if quote_id:
        quotes = Quote.objects.filter(id=quote_id)
    else:
        quotes = Quote.objects.filter(archive=False).exclude(
        id__in=Proposal.objects.all().values_list('quote_id')).order_by('-created_on')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('proposalHome')
        if form.is_valid():
            if request.POST.get("next"):
                proposal = form.save()
                predemo_calculated = proposal.quote.estimate.estimatedetails.pre_demo * 1200
                parameters = {'form': form,
                              'file_name': pdf_filename_generator(proposal.quote.estimate.id, 'P'),
                              'proposal': proposal,
                              'estimate': proposal.quote.estimate,
                              'predemo_calculated': predemo_calculated,
                              'license_owner': license_owner,
                              'owner_title': owner_title,
                              'owner_address_line1': owner_address_line1,
                              'owner_address_line2': owner_address_line2,
                              'owner_tel': owner_tel,
                              'owner_fax': owner_fax,
                              'owner_web': owner_web,
                              'owner_mail': owner_mail,
                              'owner_signature': owner_signature,
                              'owner_logo': owner_logo,
                              'user_name': user_name,
                              'user_title': user_title,
                              'user_signature': user_signature,
                              'user_cell': user_cell,
                              'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                              'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                              'company_name': company_name,
                              'WEB_URL': WEB_URL,
                              'STATIC_URL': STATIC_URL,
                              'MEDIA_URL': MEDIA_URL,
                              'os': system(),
                              }
                proposal_pdf = Proposal.create_proposal_pdf(parameters)
                parameters['proposal_pdf'] = proposal_pdf[1]
                return redirect('proposalHome')
    parameters = {'form': form,
                  'quotes': quotes
                  }
    return render(request, "proposalAdd.html", parameters)


@login_required
def estimate_delete(request, estimate_id):
    this_estimate = get_object_or_404(Estimate, id=estimate_id)
    if request.method == "POST" and request.user.is_authenticated and this_estimate.created_by == request.user:
        if request.POST.get("confirm"):
            if this_estimate.bfm:
                this_estimate.bfm.archive = False
                this_estimate.bfm.save()
            this_estimate.delete_estimate_pdf({'file_name': pdf_filename_generator(this_estimate.id, 'E')})
            this_estimate.delete()
        return redirect('estimatorHome')
    elif request.method == "POST" and request.user.is_authenticated and this_estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_estimate': this_estimate,
                'error_msg': error_msg
            }
            return render(request, "estimateDelete.html", parameters)
        return redirect('estimatorHome')
    parameters = {'this_estimate': this_estimate
                  }
    return render(request, "estimateDelete.html", parameters)


@login_required
def quote_delete(request, quote_id):
    this_quote = get_object_or_404(Quote, id=quote_id)
    if request.method == "POST" and request.user.is_authenticated and this_quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            if this_quote.estimate.bfm:
                this_quote.estimate.bfm.archive = False
                this_quote.estimate.bfm.save()
            this_quote.delete_quote_pdf({'file_name': pdf_filename_generator(this_quote.estimate.id, 'Q')})
            this_quote.delete()
        return redirect('quotationHome')
    elif request.method == "POST" and request.user.is_authenticated and this_quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_quote': this_quote,
                'error_msg': error_msg
            }
            return render(request, "quoteDelete.html", parameters)
        return redirect('quotationHome')
    parameters = {'this_quote': this_quote
                  }
    return render(request, "quoteDelete.html", parameters)


@login_required
def proposal_delete(request, proposal_id):
    this_proposal = get_object_or_404(Proposal, id=proposal_id)
    if request.method == "POST" and request.user.is_authenticated and this_proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_proposal.delete_proposal_pdf(
                {'file_name': pdf_filename_generator(this_proposal.quote.estimate.id, 'P')})
            this_proposal.delete()
        return redirect('proposalHome')
    elif request.method == "POST" and request.user.is_authenticated and this_proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_proposal': this_proposal,
                'error_msg': error_msg
            }
            return render(request, "proposalDelete.html", parameters)
        return redirect('proposalHome')
    parameters = {'this_proposal': this_proposal
                  }
    return render(request, "proposalDelete.html", parameters)


@login_required
def estimate_archive(request, estimate_id):
    this_estimate = get_object_or_404(Estimate, id=estimate_id)
    if request.method == "POST" and request.user.is_authenticated and this_estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_estimate.archive = True
            this_estimate.save()
        return redirect('estimatorHome')
    elif request.method == "POST" and request.user.is_authenticated and this_estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_estimate': this_estimate,
                'error_msg': error_msg
            }
            return render(request, "estimateArchive.html", parameters)
        return redirect('estimatorHome')
    parameters = {'this_estimate': this_estimate
                  }
    return render(request, "estimateArchive.html", parameters)


@login_required
def estimate_duplicate(request, estimate_id):
    this_estimate = get_object_or_404(Estimate, id=estimate_id)
    form = EstimateForm(request.POST or None, instance=this_estimate)
    form.fields['project'].widget = forms.HiddenInput()
    form.fields['engineer'].widget = forms.HiddenInput()
    form.fields['service'].widget = forms.HiddenInput()
    form.fields['due_date'].widget = forms.HiddenInput()
    form.fields['drawing_date'].widget = forms.HiddenInput()
    form.fields['predemo'].widget = forms.HiddenInput()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('estimatorHome')
        if request.POST.get("next"):
            duplicated_obj = deepcopy(this_estimate)
            duplicated_obj.id = None
            duplicated_obj.customer = Person.objects.get(id=request.POST.get("customer"))
            duplicated_obj.save()
            duplicated_obj.service.add(*this_estimate.service.all())

            all_equipments = EstimateEquipment.objects.filter(estimate=this_estimate)
            for equipment in all_equipments:
                equipment.pk = None
                equipment.estimate = duplicated_obj
                equipment.save()

            EstimateDetails.objects.get(estimate=duplicated_obj.pk).delete()
            estimate_detail = deepcopy(EstimateDetails.objects.get(estimate=this_estimate.pk))
            estimate_detail.id = None
            estimate_detail.estimate = duplicated_obj
            estimate_detail.save()
            return redirect('estimatorHome')
        else:
            print(form)
    parameters = {
        'form': form,
        'page_action': 'Duplicate',
    }
    return render(request, "estimatorDuplicate.html", parameters)


@login_required
def quote_archive(request, quote_id):
    this_quote = get_object_or_404(Quote, id=quote_id)
    if request.method == "POST" and request.user.is_authenticated and this_quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_quote.archive = True
            this_quote.save()
        return redirect('quotationHome')
    elif request.method == "POST" and request.user.is_authenticated and this_quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_quote': this_quote,
                'error_msg': error_msg
            }
            return render(request, "quoteArchive.html", parameters)
        return redirect('quotationHome')
    parameters = {'this_quote': this_quote
                  }
    return render(request, "quoteArchive.html", parameters)


@login_required
def proposal_archive(request, proposal_id):
    this_proposal = get_object_or_404(Proposal, id=proposal_id)
    if request.method == "POST" and request.user.is_authenticated and this_proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_proposal.archive = True
            this_proposal.save()
        return redirect('proposalHome')
    elif request.method == "POST" and request.user.is_authenticated and this_proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_proposal': this_proposal,
                'error_msg': error_msg
            }
            return render(request, "proposalArchive.html", parameters)
        return redirect('proposalHome')
    parameters = {'this_proposal': this_proposal
                  }
    return render(request, "proposalArchive.html", parameters)


@login_required
def company_customer_create_popup(request):
    form = CompanyCustomerForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_company", 0);</script>' % (instance.pk, instance))

    return render(request, "company_form.html", {"form": form})


@login_required
def company_customer_edit_popup(request, pk=None):
    instance = get_object_or_404(ContactInfo, pk=pk)
    form = CompanyCustomerForm(request.POST or None, instance=instance)
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_company", 1);</script>' % (instance.pk, instance))

    return render(request, "company_form.html", {"form": form})


@login_required
def company_engineer_create_popup(request):
    form = CompanyEngineerForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_company", 0);</script>' % (instance.pk, instance))

    return render(request, "company_form.html", {"form": form})


@login_required
def company_engineer_edit_popup(request, pk=None):
    instance = get_object_or_404(ContactInfo, pk=pk)
    form = CompanyEngineerForm(request.POST or None, instance=instance)
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_company", 1);</script>' % (instance.pk, instance))

    return render(request, "company_form.html", {"form": form})


@login_required
@csrf_exempt
def get_company_id(request):
    if request.is_ajax():
        company_name = request.GET['company_name']
        company_id = ContactInfo.objects.get(name=company_name).id
        data = {'company_id': company_id, }
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse("/")


@login_required
def customer_person_create_popup(request):
    form = CustomerForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_customer", 0);</script>' % (instance.pk, instance))

    return render(request, "customer_form.html", {"form": form})


@login_required
def customer_person_edit_popup(request, pk=None):
    instance = get_object_or_404(Person, pk=pk)
    form = CustomerForm(request.POST or None, instance=instance)
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_customer", 1);</script>' % (instance.pk, instance))

    return render(request, "customer_form.html", {"form": form})


@login_required
def engineer_person_create_popup(request):
    form = EngineerForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_customer", 0);</script>' % (instance.pk, instance))

    return render(request, "customer_form.html", {"form": form})


@login_required
def engineer_person_edit_popup(request, pk=None):
    instance = get_object_or_404(Person, pk=pk)
    form = EngineerForm(request.POST or None, instance=instance)
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_customer", 1);</script>' % (instance.pk, instance))

    return render(request, "customer_form.html", {"form": form})


@login_required
def manufacturer_person_create_popup(request):
    form = ManufacturerForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer_contact_info", 0);</script>' % (instance.pk, instance))

    return render(request, "customer_form.html", {"form": form})


@login_required
def manufacturer_person_edit_popup(request, pk=None):
    instance = get_object_or_404(Person, pk=pk)
    form = ManufacturerForm(request.POST or None, instance=instance)
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer_contact_info", 1);</script>' % (instance.pk, instance))

    return render(request, "customer_form.html", {"form": form})


@login_required
@csrf_exempt
def get_person_id(request):
    if request.is_ajax():
        person_id = request.GET['person_id']
        person_id = Person.objects.get(name=person_id).id
        data = {'person_id': person_id, }
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse("/")


@login_required
def project_create_popup(request):
    form = ProjectForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        form.cleaned_data['created_by'] = request.user
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_project", 0);</script>' % (instance.pk, instance))

    return render(request, "project_form.html", {"form": form})


@login_required
def project_edit_popup(request, pk=None):
    instance = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_project", 1);</script>' % (instance.pk, instance))

    return render(request, "project_form.html", {"form": form})


@login_required
def engineer_create_popup(request):
    form = EngineerForm(request.POST or None, initial={'created_by': request.user})
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_engineer", 0);</script>' % (instance.pk, instance))

    return render(request, "engineer_form.html", {"form": form})


@login_required
def engineer_edit_popup(request, pk=None):
    instance = get_object_or_404(Person, pk=pk)
    form = EngineerForm(request.POST or None, instance=instance)
    form.fields['created_by'].widget = forms.HiddenInput()
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_engineer", 1);</script>' % (instance.pk, instance))

    return render(request, "engineer_form.html", {"form": form})


@login_required
@csrf_exempt
def get_engineer_id(request):
    if request.is_ajax():
        engineer_id = request.GET['engineer_id']
        engineer_id = Person.objects.get(name=engineer_id).id
        data = {'person_id': engineer_id, }
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse("/")


@login_required
@csrf_exempt
def get_project_id(request):
    if request.is_ajax():
        project_name = request.GET['project_name']
        project_id = Project.objects.get(name=project_name).id
        data = {'project_id': project_id, }
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse("/")


@login_required
def estimate_equipment(request, estimate_id, estimate_service_id):
    estimate = Estimate.objects.get(id=estimate_id)
    interval_count = estimate.service.count()
    interval_set = estimate.service.all()[estimate_service_id]
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate, flag=True)
    estimate_money = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        if estimate_equipment_pricing.price_override:
            estimate_money += float(estimate_equipment_pricing.price_override) * float(
                estimate_equipment_pricing.quantity)
        else:
            estimate_money += float(estimate_equipment_pricing.equipment.price) * float(
                estimate_equipment_pricing.quantity)
    form = EquipmentForm(request.POST or None, initial={'estimate': estimate})
    form.fields['equipment'].queryset = Equipment.objects.filter(service=interval_set.id)
    form.fields['estimate'].widget = forms.HiddenInput()

    next_url = reverse('estimateDetails', kwargs={'estimate_id': estimate_id})
    next_url_text = 'Next Page'

    if estimate_service_id + 1 != interval_count:
        next_url = reverse('estimateEquipment', kwargs={'estimate_id': estimate_id,
                                                        'estimate_service_id': estimate_service_id + 1})
        next_url_text = 'Go To Next Service Equipments'
    equipments = Equipment.objects.filter(service=interval_set.id)
    equipment_in = []
    for estimate_equipment_one in estimate_equipments_pricing:
        equipment_in.append(estimate_equipment_one.equipment.id)
    if request.method == 'POST':
        if form.is_valid():
            if EstimateEquipment.objects.filter(estimate=estimate_id,
                                                equipment=form.cleaned_data['equipment']).count() == 0:
                form.cleaned_data['estimate'] = estimate
                form.save()
                estimate_money = 0
                for estimate_equipment_pricing in estimate_equipments_pricing:
                    if estimate_equipment_pricing.price_override:
                        estimate_money += float(estimate_equipment_pricing.price_override) * float(
                            estimate_equipment_pricing.quantity)
                    else:
                        estimate_money += float(estimate_equipment_pricing.equipment.price) * float(
                            estimate_equipment_pricing.quantity)
                return redirect('estimateEquipment', estimate_id, estimate_service_id)
            else:
                EstimateEquipment.objects.filter(estimate=estimate_id, equipment=form.cleaned_data['equipment']) \
                    .update(quantity=form.cleaned_data['quantity'], price_override=form.cleaned_data['price_override'])
                estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate, flag=True)
                estimate_money = 0
                for estimate_equipment_pricing in estimate_equipments_pricing:
                    if estimate_equipment_pricing.price_override:
                        estimate_money += float(estimate_equipment_pricing.price_override) * float(
                            estimate_equipment_pricing.quantity)
                    else:
                        estimate_money += float(estimate_equipment_pricing.equipment.price) * float(
                            estimate_equipment_pricing.quantity)
                return redirect('estimateEquipment', estimate_id, estimate_service_id)
    parameters = {'estimate_id': estimate_id,
                  'form': form,
                  'estimate_equipments_pricing': estimate_equipments_pricing,
                  'estimate_money': estimate_money,
                  'next_url': next_url,
                  'next_url_text': next_url_text,
                  'interval_set': interval_set,
                  'estimate_service_id': estimate_service_id,
                  'equipments': equipments,
                  'equipment_in': equipment_in
                  }
    return render(request, "estimateEquipment.html", parameters)


@login_required
def estimate_equipment_delete(request, estimate_equipment_id, interval_id):
    this_estimate_equipment = get_object_or_404(EstimateEquipment, id=estimate_equipment_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_estimate_equipment.delete()
        return redirect('estimateEquipment', this_estimate_equipment.estimate.id, interval_id)
    parameters = {'this_estimate_equipment': this_estimate_equipment
                  }
    return render(request, "estimateEquipmentDelete.html", parameters)


@login_required
def estimate_details(request, estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    instance = get_object_or_404(EstimateDetails, estimate=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate, flag=True)
    estimate_sub = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        if estimate_equipment_pricing.price_override:
            estimate_sub += float(estimate_equipment_pricing.price_override) * float(
                estimate_equipment_pricing.quantity)
        else:
            estimate_sub += float(estimate_equipment_pricing.equipment.price) * float(
                estimate_equipment_pricing.quantity)
    form = EstimateDetailsForm(request.POST or None, instance=instance,
                               initial={'estimate': estimate, 'saved_flag': True})
    form.fields['estimate'].widget = forms.HiddenInput()
    form.fields['saved_flag'].widget = forms.HiddenInput()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('estimatorHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['estimate'] = estimate
                form.cleaned_data['saved_flag'] = True
                form.save()
                if not estimate.estimatedetails.customer_adjustment:
                    estimate.estimatedetails.customer_adjustment = estimate_customer_adjustment_calculator(estimate_id)
                    estimate.estimatedetails.save()
                return redirect('estimateBid', estimate_id)
    parameters = {'estimate_id': estimate_id,
                  'estimate': estimate,
                  'form': form,
                  'estimate_equipments_pricing': estimate_equipments_pricing,
                  'estimate_sub': estimate_sub
                  }
    return render(request, "estimateDetails.html", parameters)


@login_required
def estimate_bid(request, estimate_id):
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_address_line1 = LicenseInfo.objects.get(key='OwnerAddressLine1').value
    owner_address_line2 = LicenseInfo.objects.get(key='OwnerAddressLine2').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value
    estimate = Estimate.objects.get(id=estimate_id)
    instance = get_object_or_404(EstimateDetails, estimate=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
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
    estimate_total += float(estimate.estimatedetails.customer_adjustment)
    estimate_total = round(estimate_total, 2)
    estimate_work = estimate_total_work(estimate_id)
    estimate_work_in_hours = int(estimate_work / 60)
    estimate_work_in_minutes = int(estimate_work % 60)

    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    user_signature = request.user.profile.e_sign
    if request.user.profile.cell == '' or request.user.profile.cell is None:
        user_cell = ''
    else:
        user_cell = request.user.profile.cell

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
                  'owner_address_line1': owner_address_line1,
                  'owner_address_line2': owner_address_line2,
                  'owner_tel': owner_tel,
                  'owner_fax': owner_fax,
                  'owner_web': owner_web,
                  'owner_mail': owner_mail,
                  'owner_signature': owner_signature,
                  'owner_logo': owner_logo,
                  'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                  'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                  'company_name': company_name,
                  'user_name': user_name,
                  'user_title': user_title,
                  'user_signature': user_signature,
                  'user_cell': user_cell,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'STATIC_URL': STATIC_URL,
                  'os': system(),
                  }
    estimate_pdf = Estimate.create_estimate_pdf(parameters)
    parameters['estimate_pdf'] = estimate_pdf[1]
    try:
        parameters['file_name'] = pdf_filename_generator(estimate.id, 'Q')
        parameters['quote'] = estimate.quote
        Quote.create_quote_pdf(parameters)
    except:
        pass
    try:
        parameters['file_name'] = pdf_filename_generator(estimate.id, 'P')
        parameters['proposal'] = estimate.quote.proposal
        parameters['estimate'] = estimate
        Proposal.create_proposal_pdf(parameters)
    except:
        pass

    try:
        Invoice.objects.filter(id=estimate.quote.proposal.order.invoice.id) \
            .update(times_estimate_changed=estimate.quote.proposal.order.invoice.times_estimate_changed + 1)
        total_count = InvoiceHistory.objects.filter(invoice=estimate.quote.proposal.order.invoice).count() + 1
        invoice_file_name = 'Invoice-' + str(estimate.quote.proposal.order.project_number[3:]).zfill(3) + '-' + str(
            estimate.quote.proposal.order.invoice.id).zfill(3) + '-' + str(total_count)
        parameters['file_name'] = invoice_file_name
        parameters['total_count'] = total_count
        parameters['invoice'] = estimate.quote.proposal.order.invoice
        change_orders = ChangeOrder.objects.filter(order=estimate.quote.proposal.order)
        parameters['change_orders'] = change_orders
        parameters['total_amount_due'] = calculate_total_amount_due(estimate.quote.proposal.order.invoice)
        Invoice.create_invoice_pdf(parameters)

        total_invoiced = calculate_total_amount_due(estimate.quote.proposal.order.invoice)
        total_paid = calculate_total_paid(estimate.quote.proposal.order.invoice)
        balance_due = calculate_remaining_invoice_due(estimate.quote.proposal.order.invoice)
        new_object = InvoiceHistory(invoice=estimate.quote.proposal.order.invoice, total_invoiced=total_invoiced, total_paid=total_paid,
                                    balance_due=balance_due, pdf_filename=invoice_file_name)
        new_object.save()
    except:
        pass
    return render(request, "estimateBid.html", parameters)


def estimate_total_work(estimate_id):
    estimate_equipments = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
    estimate_work = 0
    for each_estimate_equipment in estimate_equipments:
        work_total = int(each_estimate_equipment.quantity) * int(each_estimate_equipment.equipment.estimate_work)
        estimate_work += int(work_total)
    return estimate_work


def estimate_number_generator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimator_long_id = estimate.created_by.id + 100
    estimate_date_created = str(estimate.created_on).replace('-', '')[2:8]
    return estimate_date_created + str(estimator_long_id) + str(estimate.id).zfill(3)

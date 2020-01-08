from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponseRedirect
from django import forms
from .forms import *
from django.views.generic import ListView
from PyPDF2 import PdfFileMerger
import img2pdf
from PIL import Image
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, MEDIA_URL_NOSLASH
from .render import Render
import os
import random
from django.contrib.auth.decorators import login_required
from ..core.forms import EmailForm
from ..core.views import htmlbodytemplate_tag_converter
from django.core.mail import BadHeaderError, EmailMessage
import datetime
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages


def submittal_list(request):
    form = EmailForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            to_email = to_email.replace(" ", "").replace(";", ",").split(',')
            cc = form.cleaned_data['cc']
            cc = cc.replace(" ", "").replace(";", ",").split(',')
            email_id = form.cleaned_data['email_id']
            subject = form.cleaned_data['subject']
            this_submittal = get_object_or_404(CompanySubmittal, id=email_id)
            customer = this_submittal.customer
            if ModulesToEmailTemplateRelation.objects.filter(module=7).exists():
                body_content = get_object_or_404(ModulesToEmailTemplateRelation, module=7).template.content
            else:
                body_content = "There was no email template defined for 'Submittal'."
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
                    'estimator@tabtechinc.com',
                    to_email,
                    cc=cc,
                )
                msg.content_subtype = "html"
                msg.attach_file('media/pdfs/submittal/submittal-' + pdf_filename_generator(this_submittal.id) + '.pdf')
                msg.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('submittalHome')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = CompanySubmittal.objects.order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    submittals = paginator.get_page(page)

    parameters = {'submittals': submittals,
                  'form': form,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "submittal.html", parameters)


@login_required
def submittal_add(request):
    if request.method == 'POST':
        form = CompanySubmittalViewForm(request.POST)
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('submittalHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                new_submittal = form.save()
                return HttpResponseRedirect(reverse('submittalPages', args=(new_submittal.pk, )))
        else:
            form = CompanySubmittalViewForm(initial={'created_by': request.user})
    else:
        form = CompanySubmittalViewForm(initial={'created_by': request.user})
    parameters = {'form': form,
                  }
    return render(request, "submittalAdd.html", parameters)


@login_required
def submittal_pages_ordering(request, submittal_id):
    form = SubmittalFormsOrdering(request.POST or None, initial={'submittal': submittal_id})
    form.fields['submittal'].widget = forms.HiddenInput()
    submittal_forms = CompanySubmittalForm.objects.all()
    submittal_forms_selected = SubmittalForms.objects.filter(submittal=submittal_id)
    submittal_selected_in = []
    for submittal_forms_one in submittal_forms_selected:
        submittal_selected_in.append(submittal_forms_one.submittal_form.id)
    if request.method == 'POST':
        if form.is_valid():
            if SubmittalForms.objects.filter(submittal=submittal_id,
                                             ordering=form.cleaned_data['ordering']).count() == 0:
                if SubmittalForms.objects.filter(submittal=submittal_id,
                                                 submittal_form=form.cleaned_data['submittal_form']).count() == 0:
                    form.cleaned_data['submittal'] = submittal_id
                    form.save()
                    return redirect('submittalPages', submittal_id)
                else:
                    SubmittalForms.objects.filter(submittal=submittal_id, submittal_form=form.cleaned_data['submittal_form']) \
                        .update(ordering=form.cleaned_data['ordering'])
                    return redirect('submittalPages', submittal_id)
            else:
                messages.error(request, "You have selected this order number before!")
    parameters = {'form': form,
                  'submittal_forms': submittal_forms,
                  'submittal_id': submittal_id,
                  'submittal_forms_selected': submittal_forms_selected,
                  'submittal_selected_in': submittal_selected_in
                  }
    return render(request, "submittalPagesOrdering.html", parameters)


@login_required
def submittal_form_delete(request, submittal_id, submittal_form_id):
    this_submittal_form = get_object_or_404(SubmittalForms, id=submittal_form_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_submittal_form.delete()
        return redirect('submittalPages', submittal_id)
    parameters = {'this_submittal_form': this_submittal_form
                  }
    return render(request, "submittalFormDelete.html", parameters)


@login_required
def submittal_view(request, submittal_id):
    owner_name = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    owner_address = LicenseInfo.objects.get(key='OwnerAddress').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value
    submittal = CompanySubmittal.objects.get(id=submittal_id)
    submittal_forms = SubmittalForms.objects.filter(submittal=submittal_id).order_by('ordering')

    parameters = {'file_name': 'coverletter-' + pdf_filename_generator(submittal.id),
                  'submittal': submittal,
                  'owner_name': owner_name,
                  'owner_title': owner_title,
                  'owner_tel': owner_tel,
                  'owner_fax': owner_fax,
                  'owner_web': owner_web,
                  'owner_mail': owner_mail,
                  'owner_address': owner_address,
                  'owner_signature': owner_signature,
                  'company_name': company_name,
                  'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                  'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                  'request': request,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'STATIC_URL': STATIC_URL
                  }

    letterhead_output = CompanySubmittal.create_letterhead_pdf(parameters)
    merger = PdfFileMerger()
    input0 = open(letterhead_output[1], "rb")
    merger.append(fileobj=input0)
    for attachment in submittal_forms.all():
        attachment_number = random.randint(100000, 999999)
        name, extension = os.path.splitext(attachment.submittal_form.form_file.name)
        if extension == '.pdf':
            pdf_file = open(MEDIA_URL_NOSLASH + attachment.submittal_form.form_file.name, "rb")
            merger.append(fileobj=pdf_file)
        elif extension == '.jpg' or '.png' or '.jpeg':
            img_path = MEDIA_URL_NOSLASH + attachment.submittal_form.form_file.name
            image = Image.open(img_path)
            pdf_bytes = img2pdf.convert(image.filename)
            if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/imgtopdf")):
                os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/imgtopdf"))
            temp_file = open(MEDIA_URL_NOSLASH + "imgtopdf/temp" + str(attachment_number) + ".pdf", "wb")
            temp_file.write(pdf_bytes)
            temp_file = open(MEDIA_URL_NOSLASH + "imgtopdf/temp" + str(attachment_number) + ".pdf", "rb")
            merger.append(fileobj=temp_file)
    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/submittal")):
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/submittal"))
    output = open(MEDIA_URL_NOSLASH + "pdfs/submittal/" + 'submittal-' + pdf_filename_generator(submittal_id) + ".pdf", "wb")
    merger.write(output)
    parameters['submittal_url'] = MEDIA_URL + "pdfs/submittal/" + 'submittal-' + pdf_filename_generator(submittal_id) + ".pdf"
    return render(request, "submittalView.html", parameters)


@login_required
def submittal_delete(request, submittal_id):
    this_submittal = get_object_or_404(CompanySubmittal, id=submittal_id)
    if request.method == "POST" and request.user.is_authenticated and this_submittal.created_by == request.user:
        if request.POST.get("confirm"):
            this_submittal.delete_letterhead_pdf({'file_name': 'submittal-' + str(submittal_id)})
            this_submittal.delete()
        return redirect('submittalHome')
    elif request.method == "POST" and request.user.is_authenticated and this_submittal.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_estimate': this_submittal,
                'error_msg': error_msg
            }
            return render(request, "submittalDelete.html", parameters)
        return redirect('submittalHome')
    parameters = {'this_subbmital': this_submittal
                  }
    return render(request, "submittalDelete.html", parameters)



def pdf_filename_generator(submittal_id):
    submittal = CompanySubmittal.objects.get(id=submittal_id)
    estimator_long_id = submittal.created_by.id + 100
    estimate_date_created = str(submittal.created_on).replace('-', '')[2:8]
    return estimate_date_created + str(estimator_long_id) + str(submittal.id).zfill(3)
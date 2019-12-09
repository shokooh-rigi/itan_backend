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


class CompanySubmittalList(ListView):
    template_name = 'submittal.html'
    model = CompanySubmittal


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
                return HttpResponseRedirect(reverse('submittalView', args=(new_submittal.pk, )))
        else:
            form = CompanySubmittalViewForm(initial={'created_by': request.user})
    else:
        form = CompanySubmittalViewForm(initial={'created_by': request.user})
    parameters = {'form': form,
                  }
    return render(request, "submittalAdd.html", parameters)


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
    submittal = CompanySubmittal.objects.get(id=submittal_id)

    parameters = {'file_name': 'submittal-' + str(submittal_id),
                  'submittal': submittal,
                  'owner_name': owner_name,
                  'owner_title': owner_title,
                  'owner_tel': owner_tel,
                  'owner_fax': owner_fax,
                  'owner_web': owner_web,
                  'owner_mail': owner_mail,
                  'owner_address': owner_address,
                  'owner_signature': owner_signature,
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
    for attachment in submittal.submittal_form.all():
        attachment_number = random.randint(100000, 999999)
        name, extension = os.path.splitext(attachment.form_file.name)
        if extension == '.pdf':
            pdf_file = open(MEDIA_URL_NOSLASH + attachment.form_file.name, "rb")
            merger.append(fileobj=pdf_file)
        elif extension == '.jpg' or '.png' or '.jpeg':
            img_path = MEDIA_URL_NOSLASH + attachment.form_file.name
            image = Image.open(img_path)
            pdf_bytes = img2pdf.convert(image.filename)
            if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/imgtopdf")):
                os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/imgtopdf"))
            temp_file = open(MEDIA_URL_NOSLASH + "imgtopdf/temp" + str(attachment_number) + ".pdf", "wb")
            temp_file.write(pdf_bytes)
            temp_file = open(MEDIA_URL_NOSLASH + "imgtopdf/temp" + str(attachment_number) + ".pdf", "rb")
            merger.append(fileobj=temp_file)
    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/submittalforms")):
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/submittalforms"))
    output = open(MEDIA_URL_NOSLASH + "submittalforms/" + str(submittal_id) + ".pdf", "wb")
    merger.write(output)
    parameters['submittal_url'] = MEDIA_URL + "submittalforms/" + str(submittal_id) + ".pdf"
    return render(request, "submittalView.html", parameters)

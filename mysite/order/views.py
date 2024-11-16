import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django import forms
from platform import system
import os
from .forms import *
from django.conf import settings
from ..bidfilemgm.views import handle_uploaded_file, create_zip_file
from ..gi.models import *
from ..gi.views import calculate_total_amount_due, calculate_total_paid, calculate_remaining_invoice_due
import urllib.request as url_request
from django.http import HttpResponse
from mysite.sheetcreator.models import DataSheet, Sheet
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mysite.sheetcreator.models import DataSheetEquipment , SheetEquipment, SECD
from mysite.utils.pdf_to_img import pdf_to_image_bytes
from base64 import b64encode
from mysite.s3_file_manager import S3
from django.urls import reverse
from collections import OrderedDict


@login_required
def order_list(request):
    project_name = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Order.objects.filter(Q(proposal__estimate__project__name__icontains=project_name) |
                                       Q(project_number__icontains=project_name) |
                                       Q(proposal__estimate__customer__company__name__icontains=project_name)).order_by(ordering)

    if request.GET.get('type') == 'all' or request.GET.get('type') is None:
        object_list = object_list
    if request.GET.get('type') == 'inprogress':
        object_list = object_list.filter(invoice__isnull=True).filter(report__isnull=True)
    if request.GET.get('type') == 'invoiced':
        object_list = object_list.filter(invoice__isnull=False)
    if request.GET.get('type') == 'notinvoiced':
        object_list = object_list.filter(invoice__isnull=True).filter(colored_drawing__isnull=False).filter(report_colored_drawing__isnull=False)
    if request.GET.get('type') == 'reported':
        object_list = object_list.filter(report__isnull=False)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    parameters = {
        'orders': orders,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'now': datetime.datetime.now()
    }
    return render(request, "order.html", parameters)


@login_required
def order_add(request, proposal_id=None):
    form = OrderForm(request.POST or None, request.FILES or None)
    if proposal_id:
        proposals = Proposal.objects.filter(id=proposal_id)
    else:
        proposals = Proposal.objects.filter(archive=False).exclude(id__in=Order.objects.all().values_list('proposal_id')).order_by('-created_on')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.save()
                return redirect('orderHome')
    parameters = {'form': form,
                  'proposals': proposals
                  }
    return render(request, "orderAdd.html", parameters)


@login_required
def order_edit(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    proposals = Proposal.objects.filter(archive=False).exclude(id__in=Order.objects.all().values_list('proposal_id'))
    change_orders = ChangeOrder.objects.filter(order=order_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderHome')
        if request.POST.get("co"):
            return redirect('changeOrder', order_id=order_id)
        if request.POST.get("cs"):
            return redirect('controlSystem', order_id=order_id)
        if request.POST.get("es"):
            return redirect('equipmentSubmittal', order_id=order_id)
        if request.POST.get("tl"):
            return redirect('techLabel', order_id=order_id)
        if request.POST.get("ucd"):
            return redirect('fieldDrawing', order_id=order_id)
        if request.POST.get("usp"):
            return redirect('sitePictures', order_id=order_id)
        if request.POST.get("uts"):
            return redirect('testSheets', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('orderHome')
    parameters = {'form': form,
                  'proposals': proposals,
                  'change_orders': change_orders,
                  'order_id': order_id,
                  'this_order': this_order,
                  }
    return render(request, "orderEdit.html", parameters)


@login_required
def order_delete(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    if request.method == "POST" and request.user.is_authenticated and this_order.proposal.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_order.delete()
        return redirect('orderHome')
    elif request.method == "POST" and request.user.is_authenticated and this_order.proposal.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_order': this_order,
                'error_msg': error_msg
            }
            return render(request, "orderDelete.html", parameters)
        return redirect('orderHome')
    parameters = {'this_order': this_order
                  }
    return render(request, "orderDelete.html", parameters)


@login_required
def order_archive(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    if request.method == "POST" and request.user.is_authenticated and this_order.proposal.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_order.archive = True
            this_order.save()
        return redirect('orderHome')
    elif request.method == "POST" and request.user.is_authenticated and this_order.proposal.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_order': this_order,
                'error_msg': error_msg
            }
            return render(request, "orderArchive.html", parameters)
        return redirect('orderHome')
    parameters = {'this_order': this_order
                  }
    return render(request, "orderArchive.html", parameters)


@login_required
def change_order(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = ChangeOrderForm(request.POST or None, request.FILES or None, initial={'order': order_id})
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['order'] = order_id
                new_change_order = form.save()
                new_change_order.confirmed = False
                index = 0
                while request.POST.get(f"service[{index}][amount]"):
                    new_service = ChangeOrderService(change_order=new_change_order,
                                                     amount=request.POST.get(f"service[{index}][amount]"),
                                                     description=request.POST.get(f"service[{index}][description]"))
                    new_service.save()
                    index += 1

                # Create Change Order PDF here
                if request.user.last_name == '' or request.user.last_name is None:
                    user_name = 'TAB Technologies, INC. Operator'
                else:
                    user_name = request.user.first_name + " " + request.user.last_name
                if request.user.profile.title == '' or request.user.profile.title is None:
                    user_title = 'Estimator'
                else:
                    user_title = request.user.profile.title
                user_signature = request.user.profile.e_sign
                new_file_name = 'ChangeOrder-' + str(this_order.project_number[3:]).zfill(3) + '-' + new_change_order.co_number

                pdf_parameters = {
                    'file_name': new_file_name,
                    'change_order': new_change_order,
                    'change_order_services': new_change_order.changeorderservice_set.all(),
                    'order': this_order,
                    'estimate': this_order.proposal.estimate,
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
                    'WEB_URL': settings.WEB_URL,
                    'STATIC_URL': settings.STATIC_URL,
                    'MEDIA_URL': settings.MEDIA_URL,
                    'os': system(),
                }
                new_change_order.create_change_order_pdf(pdf_parameters)

                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  }
    return render(request, "changeOrder.html", parameters)


def tech_label(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    this_techlabel = TechLabel.objects.filter(order__id=order_id).first()
    extra_fields = None
    if this_techlabel:
        form = TechLabelForm(request.POST or None, instance=this_techlabel)
        extra_fields = TechLabelExtraFields.objects.filter(tech_label=this_techlabel)
    else:
        form = TechLabelForm(request.POST or None, initial={'order': order_id})

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save") or request.POST.get("savep"):
                form.cleaned_data['order'] = order_id
                this_tech_label = form.save()
                TechLabelExtraFields.objects.filter(tech_label=this_tech_label).delete()
                extra_fields_count = int(request.POST.get("extra-fields-count"))-1
                if extra_fields_count > 0:
                    for extra_field in range(extra_fields_count):
                        extra_field_title = request.POST.get("extra-field-title-" + str(extra_field+1))
                        extra_field_content = request.POST.get("extra-field-content-" + str(extra_field+1))
                        if extra_field_title and extra_field_content:
                            TechLabelExtraFields.objects.create(tech_label=this_tech_label, title=extra_field_title, content=extra_field_content)

                if request.POST.get("save"):
                    return redirect('orderEdit', order_id=order_id)
                if request.POST.get("savep"):
                    if this_tech_label.order.proposal.estimate.estimatedetails.pre_demo > 0:
                        has_pre_demo = 1
                    else:
                        has_pre_demo = 0
                    file_name = 'techlabel-' + str(this_order.project_number) + '.pdf'
                    parameters = {'form': form,
                                  'datenow': datetime.datetime.now().date(),
                                  'file_name': 'techlabel-' + str(this_order.project_number),
                                  'tech_label': this_tech_label,
                                  'extra_fields': TechLabelExtraFields.objects.filter(tech_label=this_tech_label),
                                  'has_pre_demo': has_pre_demo,
                                  'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
                                  'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
                                  'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
                                  'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                                  'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                                  'company_name': LicenseInfo.objects.get(key='CompanyName').value,
                                  'WEB_URL': settings.WEB_URL,
                                  'STATIC_URL': settings.STATIC_URL,
                                  'MEDIA_URL': settings.MEDIA_URL,
                                  'os': system(),
                                  }
                    techlabel_pdf = TechLabel.create_techlabel_pdf(parameters)
                    parameters['techlabel_pdf'] = techlabel_pdf[1]

                    s3 = S3()
                    response = url_request.urlretrieve(s3.get_bucket_object('media/pdfs/techlabel/' + file_name))
                    with open(response[0], 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type="application/pdf")
                        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_name)
                        return response
    parameters = {
        'form': form,
        'this_order': this_order,
        'extra_fields': extra_fields
    }
    return render(request, "techLabel.html", parameters)


@login_required
def control_system(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                Order.objects.filter(id=order_id).update(control_system=form.cleaned_data['control_system'])
                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  }
    return render(request, "controlSystem.html", parameters)


@login_required
def order_equipment_submittal(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):

                if request.POST.get("equipment_submittal-clear"):
                    Order.objects.filter(id=order_id).update(equipment_submittal=None)
                    return redirect('orderEdit', order_id=order_id)
                temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/order_equipment_submittal")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                files_list = request.FILES.getlist('equipment_submittal')
                files = []
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > settings.MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'page_title': 'Equipment Submittal',
                        'error_msg': error_msg
                    }
                    return render(request, "EquipmentSubmittal.html", parameters)
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    handle_uploaded_file(f, files[-1])
                project_clean_name = this_order.project_number.replace(' ', '_') \
                    .replace('!', '') \
                    .replace('@', '') \
                    .replace('#', '') \
                    .replace('$', '') \
                    .replace('%', '') \
                    .replace('^', '') \
                    .replace('&', '') \
                    .replace('*', '') \
                    .replace("/", '')
                zip_file_name = project_clean_name + '-Equipment-Submittal.zip'
                create_zip_file(files, temp_path, zip_file_name)
                file = open(temp_path + '/' + zip_file_name, 'rb')
                Order.objects.get(id=order_id).equipment_submittal.save(zip_file_name, file)

                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  'page_title': 'Equipment Submittal',
                  }
    return render(request, "EquipmentSubmittal.html", parameters)


@login_required
def order_colored_drawing(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderHome')
        if form.is_valid():
            if request.POST.get("finalize"):
                this_order.colored_drawing_finalize = True
                this_order.save()
                return redirect('orderHome')
            elif request.POST.get("save"):
                if request.POST.get("colored_drawing-clear") or request.POST.get("report_colored_drawing-clear"):
                    if request.POST.get("colored_drawing-clear"):
                        Order.objects.get(id=order_id).colored_drawing.delete()
                    if request.POST.get("report_colored_drawing-clear"):
                        Order.objects.get(id=order_id).report_colored_drawing.delete()
                else:
                    if request.FILES.getlist('colored_drawing'):
                        # temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/order_colored_drawing")
                        # if not os.path.exists(temp_path):
                        #     os.makedirs(temp_path)
                        # files_list = request.FILES.getlist('colored_drawing')
                        # files = []
                        # size_sum = 0
                        # for f in files_list:
                        #     size_sum = size_sum + f.size
                        # if size_sum > MAX_UPLOAD_SIZE:
                        #     error_msg = "Selected files exceeded maximum upload size!"
                        #     parameters = {
                        #         'form': form,
                        #         'page_title': 'Colored Drawing',
                        #         'error_msg': error_msg
                        #     }
                        #     return render(request, "ColoredDrawing.html", parameters)
                        # for f in files_list:
                        #     files.append(os.path.join(temp_path, f.name))
                        #     handle_uploaded_file(f, files[-1])
                        # project_clean_name = this_order.project_number.replace(' ', '_') \
                        #     .replace('!', '') \
                        #     .replace('@', '') \
                        #     .replace('#', '') \
                        #     .replace('$', '') \
                        #     .replace('%', '') \
                        #     .replace('^', '') \
                        #     .replace('&', '') \
                        #     .replace('*', '') \
                        #     .replace("/", '')
                        # zip_file_name = project_clean_name + '-Colored-Drawing.zip'
                        # create_zip_file(files, temp_path, zip_file_name)
                        # os.remove(Order.objects.get(id=order_id).equipment_submittal.path)
                        # file = open(temp_path + '/' + zip_file_name, 'rb')
                        # Order.objects.get(id=order_id).colored_drawing.save(zip_file_name, file)
                        this_order.save()

                    if request.FILES.getlist('report_colored_drawing'):
                        # temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/order_colored_drawing/report")
                        # if not os.path.exists(temp_path):
                        #     os.makedirs(temp_path)
                        # files_list = request.FILES.getlist('report_colored_drawing')
                        # files = []
                        # size_sum = 0
                        # for f in files_list:
                        #     size_sum = size_sum + f.size
                        # if size_sum > MAX_UPLOAD_SIZE:
                        #     error_msg = "Selected files exceeded maximum upload size!"
                        #     parameters = {
                        #         'form': form,
                        #         'page_title': 'Colored Drawing',
                        #         'error_msg': error_msg
                        #     }
                        #     return render(request, "ColoredDrawing.html", parameters)
                        # for f in files_list:
                        #     files.append(os.path.join(temp_path, f.name))
                        #     handle_uploaded_file(f, files[-1])
                        # project_clean_name = this_order.project_number.replace(' ', '_') \
                        #     .replace('!', '') \
                        #     .replace('@', '') \
                        #     .replace('#', '') \
                        #     .replace('$', '') \
                        #     .replace('%', '') \
                        #     .replace('^', '') \
                        #     .replace('&', '') \
                        #     .replace('*', '') \
                        #     .replace("/", '')
                        # zip_file_name = project_clean_name + '-Report-Colored-Drawing.zip'
                        # create_zip_file(files, temp_path, zip_file_name)
                        # # os.remove(Order.objects.get(id=order_id).equipment_submittal.path)
                        # file = open(temp_path + '/' + zip_file_name, 'rb')
                        # Order.objects.get(id=order_id).report_colored_drawing.save(zip_file_name, file)
                        this_order.save()

                return redirect('orderHome')
    parameters = {'form': form,
                  'this_order': this_order,
                  'page_title': 'Colored Drawing',
                  }
    return render(request, "ColoredDrawing.html", parameters)


@login_required
def order_field_drawing(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/field_draw")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                files_list = request.FILES.getlist('field_drawing')
                files = []
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > settings.MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'page_title': 'As Built Mechanical Plan',
                        'error_msg': error_msg
                    }
                    return render(request, "fmd.html", parameters)
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    handle_uploaded_file(f, files[-1])
                project_clean_name = this_order.project_number.replace(' ', '_') \
                    .replace('!', '') \
                    .replace('@', '') \
                    .replace('#', '') \
                    .replace('$', '') \
                    .replace('%', '') \
                    .replace('^', '') \
                    .replace('&', '') \
                    .replace('*', '') \
                    .replace("/", '')
                zip_file_name = project_clean_name + '-Field-Drawing.zip'
                create_zip_file(files, temp_path, zip_file_name)
                # os.remove(Order.objects.get(id=order_id).equipment_submittal.path)
                file = open(temp_path + '/' + zip_file_name, 'rb')
                Order.objects.get(id=order_id).field_draw.save(zip_file_name, file)

                return redirect('orderEdit', order_id=order_id)
    parameters = {
        'form': form,
        'this_order': this_order,
        'page_title': 'Field mechanical plan',
    }
    return render(request, "fmd.html", parameters)


@login_required
def order_general_notes(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # If the user clicks "cancel", redirect them back
        if request.POST.get("cancel"):
            return redirect('orderHome')

        # Manually retrieve the input values from POST request
        general_notes_and_comments = str(request.POST.get('general_notes_and_comments', ""))
        # to json string
        general_notes_and_comments = general_notes_and_comments
        # Finalize the form submission if "finalize" button is pressed
        if request.POST.get('finalize'):
            this_order.general_notes_and_comments = general_notes_and_comments
            this_order.general_notes_and_comments_finalize = True
            this_order.save()
            return redirect('orderHome')

        # Save the form if "save" button is pressed
        if request.POST.get("save"):
            this_order.general_notes_and_comments = general_notes_and_comments
            this_order.save()
            return redirect('orderHome')

    parameters = {
        'this_order': this_order,
        'page_title': 'General Notes & Comments',
    }
    return render(request, "generalNotes.html", parameters)


@login_required
def order_site_pictures(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):

                temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/order_site_pictures")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                files_list = request.FILES.getlist('site_pictures')
                files = []
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > settings.MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'page_title': 'Site Pictures',
                        'error_msg': error_msg
                    }
                    return render(request, "SitePictures.html", parameters)
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    handle_uploaded_file(f, files[-1])
                project_clean_name = this_order.project_number.replace(' ', '_') \
                    .replace('!', '') \
                    .replace('@', '') \
                    .replace('#', '') \
                    .replace('$', '') \
                    .replace('%', '') \
                    .replace('^', '') \
                    .replace('&', '') \
                    .replace('*', '') \
                    .replace("/", '')
                zip_file_name = project_clean_name + '-Site-Pictures.zip'
                create_zip_file(files, temp_path, zip_file_name)
                # os.remove(Order.objects.get(id=order_id).equipment_submittal.path)
                file = open(temp_path + '/' + zip_file_name, 'rb')
                Order.objects.get(id=order_id).site_pictures.save(zip_file_name, file)

                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  'page_title': 'Site Pictures',
                  }
    return render(request, "SitePictures.html", parameters)


@login_required
def order_test_sheets(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):

                temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/order_test_sheets")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                files_list = request.FILES.getlist('test_sheets')
                files = []
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > settings.MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'page_title': 'Test Sheets',
                        'error_msg': error_msg
                    }
                    return render(request, "TestSheets.html", parameters)
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    handle_uploaded_file(f, files[-1])
                project_clean_name = this_order.project_number.replace(' ', '_') \
                    .replace('!', '') \
                    .replace('@', '') \
                    .replace('#', '') \
                    .replace('$', '') \
                    .replace('%', '') \
                    .replace('^', '') \
                    .replace('&', '') \
                    .replace('*', '') \
                    .replace("/", '')
                zip_file_name = project_clean_name + '-Test-Sheets.zip'
                create_zip_file(files, temp_path, zip_file_name)
                # os.remove(Order.objects.get(id=order_id).equipment_submittal.path)
                file = open(temp_path + '/' + zip_file_name, 'rb')
                Order.objects.get(id=order_id).test_sheets.save(zip_file_name, file)

                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  'page_title': 'Test Sheets',
                  }
    return render(request, "TestSheets.html", parameters)


@login_required
def change_order_delete(request, order_id, change_order_id):
    this_change_order = get_object_or_404(ChangeOrder, id=change_order_id)
    this_order = get_object_or_404(Order, id=order_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            parameter = {
                'file_name': 'ChangeOrder-' + str(this_order.project_number[3:]).zfill(3) + '-' + this_change_order.co_number
            }
            this_change_order.delete_change_order_pdf(parameter)
            this_change_order.delete()
            if request.user.last_name == '' or request.user.last_name is None:
                user_name = 'TAB Technologies, INC. Operator'
            else:
                user_name = request.user.first_name + " " + request.user.last_name
            if request.user.profile.title == '' or request.user.profile.title is None:
                user_title = 'Estimator'
            else:
                user_title = request.user.profile.title
            user_signature = request.user.profile.e_sign
            change_orders = ChangeOrder.objects.filter(order=this_order.invoice.order, confirmed=True)
            total_amount_due = calculate_total_amount_due(this_order.invoice)
            total_count = InvoiceHistory.objects.filter(invoice=this_order.invoice).count() + 1
            new_file_name = 'Invoice-' + str(this_order.project_number[3:]).zfill(3) + '-' + str(
                this_order.id).zfill(3) + '-' + str(total_count)
            pdf_parameters = {
                'file_name': new_file_name,
                'total_count': total_count,
                'revision_date': InvoiceHistory.objects.filter(invoice=this_order.invoice).order_by('-id')[0],
                'invoice': this_order.invoice,
                'change_orders': change_orders,
                'total_amount_due': total_amount_due,
                'estimate': this_order.invoice.order.proposal.estimate,
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
                'WEB_URL': settings.WEB_URL,
                'STATIC_URL': settings.STATIC_URL,
                'MEDIA_URL': settings.MEDIA_URL,
                'os': system(),
            }
            Invoice.create_invoice_pdf(pdf_parameters)
            total_invoiced = calculate_total_amount_due(this_order.invoice)
            total_paid = calculate_total_paid(this_order.invoice)
            balance_due = calculate_remaining_invoice_due(this_order.invoice)
            new_object = InvoiceHistory(invoice=this_order.invoice, total_invoiced=total_invoiced,
                                        total_paid=total_paid,
                                        balance_due=balance_due, pdf_filename=new_file_name)
            new_object.save()
        return redirect('orderEdit', order_id=order_id)
    parameters = {'this_change_order': this_change_order
                  }
    return render(request, "changeOrderDelete.html", parameters)


@login_required
def approve_change_order(request, change_order_id, action):
    this_change_order = get_object_or_404(ChangeOrder, id=change_order_id)
    this_order = this_change_order.order
    if request.method == "GET" and request.user.is_authenticated:
        if action == 1:
            this_change_order.confirmed = True
        else:
            this_change_order.confirmed = False

        this_change_order.save()
        if request.user.last_name == '' or request.user.last_name is None:
            user_name = 'TAB Technologies, INC. Operator'
        else:
            user_name = request.user.first_name + " " + request.user.last_name
        if request.user.profile.title == '' or request.user.profile.title is None:
            user_title = 'Estimator'
        else:
            user_title = request.user.profile.title
        user_signature = request.user.profile.e_sign
        change_orders = ChangeOrder.objects.filter(order=this_order.invoice.order, confirmed=True)
        total_amount_due = calculate_total_amount_due(this_order.invoice)
        total_count = InvoiceHistory.objects.filter(invoice=this_order.invoice).count() + 1
        new_file_name = 'Invoice-' + str(this_order.project_number[3:]).zfill(3) + '-' + str(
            this_order.id).zfill(3) + '-' + str(total_count)
        pdf_parameters = {
            'file_name': new_file_name,
            'total_count': total_count,
            'revision_date': InvoiceHistory.objects.filter(invoice=this_order.invoice).order_by('-id')[0],
            'invoice': this_order.invoice,
            'change_orders': change_orders,
            'total_amount_due': total_amount_due,
            'estimate': this_order.invoice.order.proposal.estimate,
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
            'WEB_URL': settings.WEB_URL,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL,
            'os': system(),
        }
        Invoice.create_invoice_pdf(pdf_parameters)
        total_invoiced = calculate_total_amount_due(this_order.invoice)
        total_paid = calculate_total_paid(this_order.invoice)
        balance_due = calculate_remaining_invoice_due(this_order.invoice)
        new_object = InvoiceHistory(invoice=this_order.invoice, total_invoiced=total_invoiced,
                                    total_paid=total_paid,
                                    balance_due=balance_due, pdf_filename=new_file_name)
        new_object.save()
        return redirect('orderEdit', order_id=this_order.id)
    return redirect('orderEdit', order_id=this_order.id)


@login_required
def cs_create_popup(request):
    form = ControlSystemForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_control_system", 0);</script>' % (instance.pk, instance))

    return render(request, "cs_form.html", {"form": form})


@login_required
def cs_edit_popup(request, pk=None):
    instance = get_object_or_404(ControlSystem, pk=pk)
    form = ControlSystemForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_control_system", 1);</script>' % (instance.pk, instance))

    return render(request, "cs_form.html", {"form": form})


@login_required
def cs_manufacturer_create_popup(request):
    form = ControlSystemManufacturerForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer", 0);</script>' % (instance.pk, instance))

    return render(request, "cs_manufacturer_form.html", {"form": form})


@login_required
def manufacturer_edit_popup(request, pk=None):
    instance = get_object_or_404(ControlSystemManufacturer, pk=pk)
    form = ControlSystemManufacturerForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer", 1);</script>' % (instance.pk, instance))

    return render(request, "cs_manufacturer_form.html", {"form": form})
 
@login_required
def order_update(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    dsq = this_order.datasheet_set.all()
    sq = this_order.sheet_set.all()
    _eq_types = Equipment.objects.all()
    manufacturers = EquipmentManufacturer.objects.all()
    modules_type = "Equipments"
    eq_types = []
    for eq in _eq_types:
        eq_types.append({
            'id': eq.id,
            'name': eq.name,
            'test_sheet': eq.test_sheet.name if eq.test_sheet else None,
            'test_sheet_id': eq.test_sheet.id if eq.test_sheet else None,
        })
    _test_sheets = TestSheet.objects.all()
    test_sheets = []
    for ts in _test_sheets:
        test_sheets.append({
            'id': ts.id,
            'name': ts.name,
        })

    # ـequipments = []
    # if not dsq.exists() and not sq.exists():
    #     estimate = this_order.proposal.estimate.estimateequipment_set.all()
    #     if estimate.exists():
    #         modules_type = "Estimate"
    #         for eq in estimate:
    #             ـequipments.append({
    #                 'id': eq.id,
    #                 'equipment': eq.equipment.name,
    #                 'eq_id': eq.equipment.id,
    #                 'test_sheet': eq.equipment.test_sheet.name if eq.equipment.test_sheet else None,
    #                 'test_sheet_id': eq.equipment.test_sheet.id if eq.equipment.test_sheet else None,
    #                 'service': eq.estimate.service.name,
    #                 'qty': int(eq.quantity),
    #             })
    # else:
    #     equipments_dict = {}
    #     for ds in dsq:
    #         equipments = ds.datasheetequipment_set.all()
    #         for eq in equipments:
    #             key = (eq.equipment_type.id, eq.sheet.test_sheet_type.id)
    #             if key in equipments_dict:
    #                 equipments_dict[key]['qty'] += 1
    #                 equipments_dict[key]['qty_range'] = range(equipments_dict[key]['qty'])
    #                 equipments_dict[key]['eqdbs'].append(eq.equipment)
    #                 equipments_dict[key]['eqs'].append(eq)
    #             else:
    #                 equipments_dict[key] = {
    #                     'id': eq.id,
    #                     'equipment': eq.equipment_type.name,
    #                     'eq_id': eq.equipment_type.id,
    #                     'test_sheet': eq.sheet.test_sheet_type.name,
    #                     'test_sheet_id': eq.sheet.test_sheet_type.id,
    #                     'eqdbs': [eq.equipment],
    #                     'service': eq.equipment.equipment_type.service.name,
    #                     'eqs': [eq],
    #                     'qty': 1,
    #                     'qty_range': range(1),
    #                     'type': 'datasheetequipment',
    #                     # 
    #                     'general_url': None,
    #                     'design_url': None,
    #                     'actual_url': None,
    #                     'general_colour': None,
    #                     'design_colour': None,
    #                     'actual_colour': None,
    #                     'general_disabled': '',
    #                     'design_disabled': '',
    #                     'actual_disabled': ''
    #                 }
    #                 if eq.sheet.test_sheet_type.name.lower() == "air moving":
    #                     equipments_dict[key]['general_url'] = reverse('sheetEquipmentCommonData', args=[eq.id])
    #                     # equipments_dict[key]['general_url'] = reverse('sheetEquipmentCommonDataEdit', args=[eq.id])
    #                     equipments_dict[key]['design_url'] = reverse('sheetEquipmentDesignValue', args=[eq.id])
    #                     equipments_dict[key]['actual_url'] = reverse('sheetEquipmentActualValue', args=[eq.id])
    #                     # equipments_dict[key]['actual_url'] = reverse('sheetEquipmentActualValueEdit', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "air moving equipment":
    #                 #     equipments_dict[key]['general_url'] = reverse('airMovingEquipmentCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('airMovingEquipmentDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('airMovingEquipmentActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "chiller":
    #                 #     equipments_dict[key]['general_url'] = reverse('chillerCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('chillerDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('chillerActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "dalt":
    #                 #     equipments_dict[key]['design_url'] = reverse('daltDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('daltActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "flow measuring":
    #                 #     equipments_dict[key]['general_url'] = reverse('flowCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('flowDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('flowActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "hot water boiler":
    #                 #     equipments_dict[key]['general_url'] = reverse('hotWaterBoilerCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('hotWaterBoilerDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('hotWaterBoilerActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "induction unit":
    #                 #     equipments_dict[key]['design_url'] = reverse('inductionUnitDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('inductionUnitActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "primary heat exchanger":
    #                 #     equipments_dict[key]['general_url'] = reverse('primaryHeatExchangerCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('primaryHeatExchangerDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('primaryHeatExchangerActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "primary heat exchanger 2":
    #                 #     equipments_dict[key]['general_url'] = reverse('primaryHeatExchanger2CommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('primaryHeatExchanger2DesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('primaryHeatExchanger2ActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "pitot traverse summary":
    #                 #     equipments_dict[key]['design_url'] = reverse('pitotTraverseSummaryDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('pitotTraverseSummaryActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "pump":
    #                 #     equipments_dict[key]['general_url'] = reverse('pumpCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('pumpDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('pumpActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "terminal":
    #                 #     equipments_dict[key]['design_url'] = reverse('terminalSheetEquipmentDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('terminalSheetEquipmentActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "vav":
    #                 #     equipments_dict[key]['general_url'] = reverse('vavSheetEquipmentGeneralData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('vavSheetEquipmentDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('vavSheetEquipmentActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "vav box fan heat schedule":
    #                 #     equipments_dict[key]['design_url'] = reverse('vbfhsDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('vbfhsActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "v.a.v. box schedule":
    #                 #     equipments_dict[key]['design_url'] = reverse('vbsCommonData', args=[eq.id])
    #                 #     equipments_dict[key]['design_url'] = reverse('vbfhsDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('vbfhsActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "v.a.v. box temperature schedule":
    #                 #     equipments_dict[key]['design_url'] = reverse('vbtsDesignData', args=[eq.id])
    #                 #     equipments_dict[key]['actual_url'] = reverse('vbtsActualData', args=[eq.id])
    #                 # elif eq.sheet.test_sheet_type.name.lower() == "velocity traverse":
    #                 #     equipments_dict[key]['actual_url'] = reverse('velocityActualData', args=[eq.id])
    #                 else:
    #                     equipments_dict[key]['general_url'] = reverse('vavSheetEquipmentGeneralData', args=[eq.id])
    #                     # equipments_dict[key]['design_url'] = reverse('terminalSheetEquipmentDesignData', args=[eq.sheet.id, eq.id])
    #                     # equipments_dict[key]['actual_url'] = reverse('terminalSheetEquipmentActualData', args=[eq.sheet.id, eq.id])
    #                     equipments_dict[key]['design_url'] = reverse('vavSheetEquipmentDesignData', args=[eq.id])
    #                     equipments_dict[key]['actual_url'] = reverse('vavSheetEquipmentActualData', args=[eq.id])

    #                 # if updated
    #                 if eq.main_data_entry_completed:
    #                     equipments_dict[key]['general_colour'] = '#FFA500'
    #                 else:
    #                     equipments_dict[key]['general_colour'] = '#0000FF'
    #                 if eq.design_data_entry_completed:
    #                     equipments_dict[key]['design_colour'] = '#FFA500'
    #                 else:
    #                     equipments_dict[key]['design_colour'] = '#0000FF'
    #                 if eq.actual_data_entry_completed:
    #                     equipments_dict[key]['actual_colour'] = '#FFA500'
    #                 else:
    #                     equipments_dict[key]['actual_colour'] = '#0000FF'
    #                 # # if confirmed
    #                 # if eq.main_data_entry_confirmed:
    #                 #     equipments_dict[key]['general_colour'] = '#008000'
    #                 #     equipments_dict[key]['general_disabled'] = 'disabled-link'
    #                 # if eq.design_data_entry_confirmed:
    #                 #     equipments_dict[key]['design_colour'] = '#008000'
    #                 #     equipments_dict[key]['design_disabled'] = 'disabled-link'
    #                 # if eq.actual_data_entry_confirmed:
    #                 #     equipments_dict[key]['actual_colour'] = '#008000'
    #                 #     equipments_dict[key]['actual_disabled'] = 'disabled-link'

    #     for s in sq:
    #         equipments = s.sheetequipment_set.all()
    #         for eq in equipments:
    #             key = (eq.equipment_type.id, eq.sheet.test_sheet_type.id)
    #             if key in equipments_dict:
    #                 equipments_dict[key]['qty'] += 1
    #                 equipments_dict[key]['qty_range'] = range(equipments_dict[key]['qty'])
    #                 equipments_dict[key]['eqdbs'].append(eq.equipment)
    #                 equipments_dict[key]['eqs'].append(eq)
    #             else:
    #                 equipments_dict[key] = {
    #                     'id': eq.id,
    #                     'equipment': eq.equipment_type.name,
    #                     'eq_id': eq.equipment_type.id,
    #                     'test_sheet': eq.sheet.test_sheet_type.name,
    #                     'test_sheet_id': eq.sheet.test_sheet_type.id,
    #                     'eqdbs': [eq.equipment],
    #                     'service': eq.equipment.equipment_type.service.name,
    #                     'eqs': [eq],
    #                     'qty': 1,
    #                     'qty_range': range(1),
    #                     'type': 'sheetequipment',
    #                     # 
    #                     'general_url': reverse('sheetEquipmentCommonData', args=[eq.id]),
    #                     # 'general_url': reverse('sheetEquipmentCommonDataEdit', args=[eq.id]),
    #                     'design_url': reverse('sheetEquipmentDesignValue', args=[eq.id]),
    #                     'actual_url': reverse('sheetEquipmentActualValue', args=[eq.id]),
    #                     # 'actual_url': reverse('sheetEquipmentActualValueEdit', args=[eq.id]),
    #                     'general_colour': None,
    #                     'design_colour': None,
    #                     'actual_colour': None,
    #                     'general_disabled': '',
    #                     'design_disabled': '',
    #                     'actual_disabled': ''
    #                 }
    #                 # if updated
    #                 if eq.main_data_entry_completed:
    #                     equipments_dict[key]['general_colour'] = '#FFA500'
    #                 else:
    #                     equipments_dict[key]['general_colour'] = '#0000FF'
    #                 if eq.design_data_entry_completed:
    #                     equipments_dict[key]['design_colour'] = '#FFA500'
    #                 else:
    #                     equipments_dict[key]['design_colour'] = '#0000FF'
    #                 if eq.actual_data_entry_completed:
    #                     equipments_dict[key]['actual_colour'] = '#FFA500'
    #                 else:
    #                     equipments_dict[key]['actual_colour'] = '#0000FF'
    #                 # # if confirmed
    #                 # if eq.main_data_entry_confirmed:
    #                 #     equipments_dict[key]['general_colour'] = '#008000'
    #                 #     equipments_dict[key]['general_disabled'] = 'disabled-link'
    #                 # if eq.design_data_entry_confirmed:
    #                 #     equipments_dict[key]['design_colour'] = '#008000'
    #                 #     equipments_dict[key]['design_disabled'] = 'disabled-link'
    #                 # if eq.actual_data_entry_confirmed:
    #                 #     equipments_dict[key]['actual_colour'] = '#008000'
    #                 #     equipments_dict[key]['actual_disabled'] = 'disabled-link'
                    
    #     ـequipments = list(equipments_dict.values())
    # sorted_ـequipments = []
    # for eq in ـequipments:
    #     if not eq['service']:
    #         continue
    #     if 'air balancing' == eq['service'].lower():
    #         sorted_ـequipments.append(eq)
    # for eq in ـequipments:
    #     if not eq['service']:
    #         continue
    #     if 'water balancing' == eq['service'].lower():
    #         sorted_ـequipments.append(eq)
    # for eq in ـequipments:
    #     if eq not in sorted_ـequipments:
    #         sorted_ـequipments.append(eq)

    ـequipments = []
    if not dsq.exists() and not sq.exists():
        estimate = this_order.proposal.estimate.estimateequipment_set.all()
        if estimate.exists():
            modules_type = "Estimate"
            for eq in estimate:
                ـequipments.append({
                    'id': eq.id,
                    'equipment': eq.equipment.name,
                    'eq_id': eq.equipment.id,
                    'test_sheet': eq.equipment.test_sheet.name if eq.equipment.test_sheet else None,
                    'test_sheet_id': eq.equipment.test_sheet.id if eq.equipment.test_sheet else None,
                    'service': eq.estimate.service.name,
                    'qty': int(eq.quantity),
                })
    else:
        equipments_dict = {}

        air_terminal = DataSheet.objects.filter(project=this_order, test_sheet_type__name__icontains='terminal')
        if air_terminal.exists():
            air_terminal = air_terminal[0].id

        for ds in dsq:
            equipments = ds.datasheetequipment_set.all()
            for eq in equipments:
                key = (eq.equipment_type.id, eq.sheet.test_sheet_type.id)
                if key in equipments_dict:
                    equipments_dict[key]['qty'] += 1
                    equipments_dict[key]['qty_range'] = range(equipments_dict[key]['qty'])
                    # equipments_dict[key]['eqdbs'].append(eq.equipment)
                    equipments_dict[key]['eqs'].append(eq)
                else:
                    equipments_dict[key] = {
                        'id': eq.id,
                        'equipment': eq.equipment_type.name,
                        'eq_id': eq.equipment_type.id,
                        'sheet': eq.sheet,
                        'test_sheet': eq.sheet.test_sheet_type.name,
                        'test_sheet_id': eq.sheet.test_sheet_type.id,
                        'air_terminal_ds': air_terminal,
                        # 'eqdbs': [eq.equipment],
                        'service': eq.equipment.equipment_type.service.name,
                        'eqs': [eq],
                        'qty': 1,
                        'qty_range': range(1),
                        'type': 'datasheetequipment',
                        # 
                        'general_url': None,
                        'design_url': None,
                        'actual_url': None,
                        'general_colour': None,
                        'design_colour': None,
                        'actual_colour': None,
                    }
                if eq.sheet.test_sheet_type.name.lower() == "air moving":
                    if not eq.equipment.main_data_entry_confirmed:
                        equipments_dict[key]['general_url'] = reverse('sheetEquipmentCommonData', args=[eq.id])
                    else:
                        equipments_dict[key]['general_url'] = reverse('sheetEquipmentCommonDataEdit', args=[eq.id])
                    equipments_dict[key]['design_url'] = reverse('sheetEquipmentDesignValue', args=[eq.id])
                    if not eq.equipment.actual_data_entry_confirmed:
                        equipments_dict[key]['actual_url'] = reverse('sheetEquipmentActualValue', args=[eq.id])
                    else:
                        equipments_dict[key]['actual_url'] = reverse('sheetEquipmentActualValueEdit', args=[eq.id])
                else:
                    equipments_dict[key]['general_url'] = reverse('vavSheetEquipmentGeneralData', args=[eq.id])
                    equipments_dict[key]['design_url'] = reverse('vavSheetEquipmentDesignData', args=[eq.id])
                    equipments_dict[key]['actual_url'] = reverse('vavSheetEquipmentActualData', args=[eq.id])
                # # if updated
                # if eq.main_data_entry_completed:
                #     equipments_dict[key]['general_colour'] = '#FFA500'
                # else:
                #     equipments_dict[key]['general_colour'] = '#0000FF'
                # if eq.design_data_entry_completed:
                #     equipments_dict[key]['design_colour'] = '#FFA500'
                # else:
                #     equipments_dict[key]['design_colour'] = '#0000FF'
                # if eq.actual_data_entry_completed:
                #     equipments_dict[key]['actual_colour'] = '#FFA500'
                # else:
                #     equipments_dict[key]['actual_colour'] = '#0000FF'
                # if confirmed
                if eq.equipment.main_data_entry_confirmed:
                    equipments_dict[key]['general_colour'] = '#008000'
                if eq.equipment.design_data_entry_confirmed:
                    equipments_dict[key]['design_colour'] = '#008000'
                if eq.equipment.actual_data_entry_confirmed:
                    equipments_dict[key]['actual_colour'] = '#008000'

        for s in sq:
            equipments = s.sheetequipment_set.all()
            for eq in equipments:
                key = (eq.equipment_type.id, eq.sheet.test_sheet_type.id)
                if key in equipments_dict:
                    equipments_dict[key]['qty'] += 1
                    equipments_dict[key]['qty_range'] = range(equipments_dict[key]['qty'])
                    # equipments_dict[key]['eqdbs'].append(eq.equipment)
                    equipments_dict[key]['eqs'].append(eq)
                else:
                    equipments_dict[key] = {
                        'id': eq.id,
                        'equipment': eq.equipment_type.name,
                        'eq_id': eq.equipment_type.id,
                        'sheet': eq.sheet,
                        'test_sheet': eq.sheet.test_sheet_type.name,
                        'test_sheet_id': eq.sheet.test_sheet_type.id,
                        'air_terminal_ds': air_terminal,
                        # 'eqdbs': [eq.equipment],
                        'service': eq.equipment.equipment_type.service.name,
                        'eqs': [eq],
                        'qty': 1,
                        'qty_range': range(1),
                        'type': 'sheetequipment',
                        # 
                        'general_url': reverse('sheetEquipmentCommonData', args=[eq.id]),
                        # 'general_url': reverse('sheetEquipmentCommonDataEdit', args=[eq.id]),
                        'design_url': reverse('sheetEquipmentDesignValue', args=[eq.id]),
                        'actual_url': reverse('sheetEquipmentActualValue', args=[eq.id]),
                        'general_colour': None,
                        'design_colour': None,
                        'actual_colour': None,
                    }
                    # if updated
                    if eq.main_data_entry_completed:
                        equipments_dict[key]['general_colour'] = '#FFA500'
                    else:
                        equipments_dict[key]['general_colour'] = '#0000FF'
                    if eq.design_data_entry_completed:
                        equipments_dict[key]['design_colour'] = '#FFA500'
                    else:
                        equipments_dict[key]['design_colour'] = '#0000FF'
                    if eq.actual_data_entry_completed:
                        equipments_dict[key]['actual_colour'] = '#FFA500'
                    else:
                        equipments_dict[key]['actual_colour'] = '#0000FF'
                    # # if confirmed
                    # if eq.main_data_entry_confirmed:
                    #     equipments_dict[key]['general_colour'] = '#008000'
                    #     equipments_dict[key]['general_disabled'] = 'disabled-link'
                    # if eq.design_data_entry_confirmed:
                    #     equipments_dict[key]['design_colour'] = '#008000'
                    #     equipments_dict[key]['design_disabled'] = 'disabled-link'
                    # if eq.actual_data_entry_confirmed:
                    #     equipments_dict[key]['actual_colour'] = '#008000'
                    #     equipments_dict[key]['actual_disabled'] = 'disabled-link'
                    
        ـequipments = list(equipments_dict.values())
    sorted_equipments = []
    for eq in ـequipments:
        if 'Air Balancing' == eq['service']:
            sorted_equipments.append(eq)
    for eq in ـequipments:
        if 'Water Balancing' == eq['service']:
            sorted_equipments.append(eq)
    for eq in ـequipments:
        if eq not in sorted_equipments:
            sorted_equipments.append(eq)

    # service_order = ['Air Balancing', 'Water Balancing']
    # sorted_equipments = OrderedDict()
    # for service in service_order:
    #     sorted_equipments[service] = []
    # for eq in ـequipments:
    #     service = eq['service']
    #     if service in sorted_equipments:
    #         sorted_equipments[service].append(eq)
    #     else:
    #         if service not in sorted_equipments:
    #             sorted_equipments[service] = [eq]

    _s3 = S3()
    image_data_list = []
    # for _fl in [
    #     this_order.equipment_submittal, 
    #     this_order.colored_drawing, 
    #     this_order.report_colored_drawing, 
    #     this_order.field_draw, 
    #     this_order.site_pictures,
    #     this_order.test_sheets
    # ]:
    #     if not _fl:
    #         continue
    #     if _fl.name.endswith('.pdf'):
    #         _fl_path = _s3.get_bucket_object("media/" + _fl.name)
    #         image_bytes_list = pdf_to_image_bytes(_fl_path)
    #         image_data_list = [b64encode(img_bytes).decode('utf-8') for img_bytes in image_bytes_list]
    #     else:
    #         image_data_list.append(_fl_path)

    context = {
        "order": this_order,
        "equipments": sorted_equipments,
        "eq_types": eq_types,
        "test_sheets": test_sheets,
        "maps": image_data_list,
        "modules_type": modules_type,
        "manufacturers": manufacturers,
    }
    return render(request, "order_edit_new.html", context)

@csrf_exempt
@require_http_methods(["POST"])
def create_datasheets(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    data = json.loads(request.body)['data']

    for item in data:
        # check if it was RGD skip
        if "RGD" in item['equipment']:
            continue
        equipment = get_object_or_404(Equipment, name=item['equipment'])
        if item['test_sheet'] == 'None':
            test_sheet_instance = get_object_or_404(TestSheet, name__iexact=item['equipment'].split()[0].lower())
        else:
            test_sheet_instance = get_object_or_404(TestSheet, name=item['test_sheet'])
        # if 'air moving' in test_sheet_instance.name.lower():
        if test_sheet_instance.name.lower() == 'air moving':
            if order.sheet_set.exists():
                sheet = order.sheet_set.filter(test_sheet_type=test_sheet_instance)
                if sheet.filter(sheetequipment__equipment_type=equipment).exists():
                    return JsonResponse({'status': 'error', 'message': 'Equipment already exists in the datasheet'}, status=400)
                sheet = sheet.first()
            else:
                sheet = Sheet.objects.create(
                    project=order,
                    test_sheet_type=test_sheet_instance,
                    sheet_date=datetime.datetime.now().date(),
                )
        else:
            datasheet = order.datasheet_set.filter(test_sheet_type=test_sheet_instance)
            if datasheet.filter(datasheetequipment__equipment_type=equipment).exists():
                return JsonResponse({'status': 'error', 'message': 'Equipment already exists in the datasheet'}, status=400)
            if not datasheet.exists():
                datasheet = DataSheet.objects.create(
                    test_sheet_type=test_sheet_instance,
                    project=order,
                    number_of_equipment_groups=int(item['qty']),
                    sheet_date=datetime.datetime.now().date(),
                )
            else:
                datasheet = datasheet.first()
                datasheet.number_of_equipment_groups += int(item['qty'])
                datasheet.save()

        for i in range(int(item['qty'])):
            eqdb = EquipmentDb.objects.create(
                equipment_type=equipment,
            )
            # if 'air moving' in test_sheet_instance.name.lower():
            if test_sheet_instance.name.lower() == 'air moving':
                eq = SheetEquipment.objects.create(
                    sheet=sheet,
                    equipment_type=equipment,
                    equipment=eqdb,
                )
            else:
                eq = DataSheetEquipment.objects.create(
                    sheet=datasheet,
                    equipment_type=equipment,
                    equipment=eqdb,
                )
    return JsonResponse({'status': 'success'}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def delete_datasheet(request, order_id):
    data = json.loads(request.body)['data']
    order = get_object_or_404(Order, id=order_id)
    equipments = []

    if data['type'] == 'datasheetequipment':
        equipments = order.datasheet_set.filter(
            test_sheet_type__id=data['test_sheet_id']).first().datasheetequipment_set.filter(
            equipment_type__id=data['eq_type_id'],
        )
    if data['type'] == 'sheetequipment':
        equipments = order.sheet_set.filter(
            test_sheet_type__id=data['test_sheet_id']).first().sheetequipment_set.filter(
            equipment_type__id=data['eq_type_id'],
        )
    for eq in equipments:
        try:
            eq.equipment.delete()
        except Exception as e:
            print(e)
        eq.delete()
    if data['type'] == 'datasheetequipment':
        datasheets = DataSheet.objects.filter(test_sheet_type__id=data['test_sheet_id'])
        for datasheet in datasheets:
            if not datasheet.datasheetequipment_set.exists():
                datasheet.delete()
    if data['type'] == 'sheetequipment':
        sheets = Sheet.objects.filter(test_sheet_type__id=data['test_sheet_id'])
        for sheet in sheets:
            if not sheet.sheetequipment_set.exists():
                sheet.delete()
    return JsonResponse({'status': 'success'}, status=200)


@csrf_exempt
@require_http_methods(["DELETE"])
def clear_datasheets(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    datasheets = order.datasheet_set.all()
    for datasheet in datasheets:
        equipments = datasheet.datasheetequipment_set.all()
        for eq in equipments:
            eq.equipment.delete()
            eq.delete()
        datasheet.delete()
    sheetequipments = order.sheet_set.all()
    for sheet in sheetequipments:
        equipments = sheet.sheetequipment_set.all()
        for eq in equipments:
            eq.equipment.delete()
            eq.delete()
        sheet.delete()
    return JsonResponse({'status': 'success'}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def create_datasheet(request, order_id):
    data = json.loads(request.body)['data']
    order = get_object_or_404(Order, id=order_id)
    test_sheet = get_object_or_404(TestSheet, id=data['eq_type'])
    equipment = get_object_or_404(Equipment, id=data['eq'])

    # if 'air moving' in test_sheet.name.lower():
    if test_sheet.name.lower() == 'air moving':
        sheet = order.sheet_set.filter(test_sheet_type=test_sheet)
        if sheet.filter(sheetequipment__equipment_type=equipment).exists():
            return JsonResponse({'status': 'error', 'message': 'Equipment already exists in the datasheet'}, status=400)
        if not sheet.exists():
            sheet = Sheet.objects.create(
                project=order,
                test_sheet_type=test_sheet,
            )
        else:
            sheet = sheet.first()
    else:
        datasheet = order.datasheet_set.filter(test_sheet_type=test_sheet)
        if datasheet.filter(datasheetequipment__equipment_type=equipment).exists():
            return JsonResponse({'status': 'error', 'message': 'Equipment already exists in the datasheet'}, status=400)
        if not datasheet.exists():
            datasheet = DataSheet.objects.create(
                test_sheet_type=test_sheet,
                project=order,
                number_of_equipment_groups=int(data['eq_count']),
                sheet_date=datetime.datetime.now().date(),
            )
        else:
            datasheet = datasheet.first()
            datasheet.number_of_equipment_groups += int(data['eq_count'])
            datasheet.save()
        
    for i in range(int(data['eq_count'])):
        eqdb = EquipmentDb.objects.create(
            equipment_type=equipment,
        )
        # if 'air moving' in test_sheet.name.lower():
        if test_sheet.name.lower() == 'air moving':
            eq = SheetEquipment.objects.create(
                sheet=sheet,
                equipment_type=equipment,
                equipment=eqdb,
            )
        else:
            eq = DataSheetEquipment.objects.create(
                sheet=datasheet,
                equipment_type=equipment,
                equipment=eqdb,
            )
    return JsonResponse({'status': 'success'}, status=200)

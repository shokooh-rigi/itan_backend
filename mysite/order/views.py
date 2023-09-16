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
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, MAX_UPLOAD_SIZE, UPLOAD_URL
from ..bidfilemgm.views import handle_uploaded_file, create_zip_file
from ..gi.models import *
from ..gi.views import calculate_total_amount_due, calculate_total_paid, calculate_remaining_invoice_due
from ..s3_file_manager import S3
import urllib.request as url_request


# Create your views here.


@login_required
def order_list(request):
    project_name = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Order.objects.filter(Q(proposal__quote__estimate__project__name__icontains=project_name) |
                                       Q(project_number__icontains=project_name) |
                                       Q(proposal__quote__estimate__customer__company__name__icontains=project_name)).order_by(ordering)

    if request.GET.get('type') == 'all' or request.GET.get('type') is None:
        object_list = object_list
    if request.GET.get('type') == 'inprogress':
        object_list = object_list.filter(invoice__isnull=True).filter(report__isnull=True)
    if request.GET.get('type') == 'invoiced':
        object_list = object_list.filter(invoice__isnull=False)
    if request.GET.get('type') == 'notinvoiced':
        object_list = object_list.filter(invoice__isnull=True).filter(report__isnull=False)
    if request.GET.get('type') == 'reported':
        object_list = object_list.filter(report__isnull=False)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    parameters = {'orders': orders,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
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
    if request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_order.delete()
        return redirect('orderHome')
    elif request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by != request.user:
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
    if request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_order.archive = True
            this_order.save()
        return redirect('orderHome')
    elif request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by != request.user:
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
                    'estimate': this_order.proposal.quote.estimate,
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
                    if this_tech_label.order.proposal.quote.estimate.estimatedetails.pre_demo > 0:
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
                                  'WEB_URL': WEB_URL,
                                  'STATIC_URL': STATIC_URL,
                                  'MEDIA_URL': MEDIA_URL,
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
                if size_sum > MAX_UPLOAD_SIZE:
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
                if size_sum > MAX_UPLOAD_SIZE:
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
    form = GeneralNoteForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderHome')
        if form.is_valid():
            if request.POST.get('finalize'):
                this_order.general_notes_and_comments_finalize = True
                this_order.save()
                return redirect('orderHome')
            if request.POST.get("save"):
                form.save()
                return redirect('orderHome')
    parameters = {
        'form': form,
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
                if size_sum > MAX_UPLOAD_SIZE:
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
                if size_sum > MAX_UPLOAD_SIZE:
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
                'estimate': this_order.invoice.order.proposal.quote.estimate,
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
            'estimate': this_order.invoice.order.proposal.quote.estimate,
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


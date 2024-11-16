import re
from typing import Dict
import math
import os
from itertools import chain
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from .render import Render as PDFRender
from django.conf import settings
from ..sheetcreator.models import *
from django.db.models import Count
from .models import VelocitySheetData, VelocitySheetTableData, VelocityEquipment

from multiprocessing import Pool


# Create your views here.


@login_required
def velocity_sheet_list(request):
    search = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__icontains='traverse')
    object_list = object_list.filter(Q(project__proposal__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  }
    return render(request, "velocityList.html", parameters)


@login_required
def velocity_sheet_add(request):
    form = VelocitySheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.filter(sheet__isnull=False).exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__icontains='traverse').values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('velocitySheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='traverse')
                sheet.save()

                return redirect('velocitySheetEquipmentList', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "velocitySheetAdd.html", parameters)


@login_required
def velocity_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    my_project = my_sheet.project
    air_moving_sheet_equipments = SheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='air mov', sheet__project=my_project)
    air_moving_sheet_equipments = air_moving_sheet_equipments.filter(secd__value__icontains=project_name).distinct().order_by('-velocity_data').distinct()
    parameters = {'air_moving_sheet_equipments': air_moving_sheet_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  }
    return render(request, "velocitySheetEquipmentsList.html", parameters)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    air_moving_equipments = SheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='air mov', sheet__project=my_sheet.project).all()
    velocity_equipments = []
    for air_moving_equipment in air_moving_equipments:
        for velocity_equipment in air_moving_equipment.velocityequipment_set.filter(velocity_data=True):
            velocity_equipment_obj = {}
            for velocity_data in velocity_equipment.velocitysheetdata_set.all():
                velocity_equipment_obj[velocity_data.sheet_field.field_name] = velocity_data.value
            velocity_equipment_obj['equipment_id'] = velocity_equipment.id
            velocity_equipments.append(velocity_equipment_obj)

    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    return {
        'max_row': range(14),
        'max_col': range(14),
        'form': {
            'my_sheet': my_sheet,
            'air_moving_equipments': air_moving_equipments,
            'velocity_equipments': velocity_equipments
        },
        'file_name': 'Velocity Sheet {}-{}{}'.format(my_sheet.project.proposal.estimate.project.name,
                                                     my_sheet.project.project_number,
                                                     '' if is_report_pdf else ' TECH').upper(),
        'license_owner': license_owner,
        'owner_title': owner_title,
        'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
        'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
        'owner_tel': owner_tel,
        'owner_fax': owner_fax,
        'owner_web': owner_web,
        'owner_mail': owner_mail,
        'owner_signature': owner_signature,
        'owner_logo': owner_logo,
        'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
        'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
        'company_name': company_name,
        'WEB_URL': settings.WEB_URL,
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'os': system(),
    }


@login_required
def equipments_generate_report_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, True)

    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/velocitySheetEquipmentTemplate.html', parameters,
                                                  'velocityEquipmentReport')


    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as fh:
            my_file = fh.read()
            response = HttpResponse(my_file, content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + pdf_name
            response['Content-Length'] = len(my_file)
            return response
    else:
        return 'error'


def split(value: str, sep: str):
    return value.replace(' ', '').split(sep)


def contains(value: str, sub: str):
    return value.find(sub) != -1


def manual_replace(s, char, index):
    return s[:index] + char + s[index +1:]


@login_required
def velocity_add_equipment(request, sheet_id, sheet_equipment_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    new_velocity_equipment = VelocityEquipment(air_moving_equipment_id=sheet_equipment_id)
    new_velocity_equipment.save()
    new_velocity_equipment.air_moving_equipment.velocity_data = True
    new_velocity_equipment.air_moving_equipment.save()

    return redirect('velocitySheetEquipmentList', my_sheet.id)


@login_required
def velocity_actual_data(request, sheet_id, velocity_equipment_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    velocity_equipment = get_object_or_404(VelocityEquipment, id=velocity_equipment_id)

    equipment_type = 1
    this_sheet_equipment = get_object_or_404(SheetEquipment, id=velocity_equipment.air_moving_equipment.id)
    sheet_code = this_sheet_equipment.secd_set.get(key__column_title__icontains='fan no.').value

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='traverse')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('velocitySheetEquipmentList', my_sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = VelocitySheetData.objects.filter(velocity_equipment=velocity_equipment,
                                                               sheet_field=actual_field).count()

                if num_results > 0:
                    VelocitySheetData.objects.filter(velocity_equipment=velocity_equipment,
                                                     sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = VelocitySheetData(velocity_equipment=velocity_equipment,
                                                   sheet_field=actual_field,
                                                   value=new_value)
                    new_object.save()

            table_row = int(request.POST.get('table-row'))
            table_col = int(request.POST.get('table-col'))

            old_velocity_table_data = VelocitySheetTableData.objects.filter(velocity_equipment=velocity_equipment)
            for velocity_data in old_velocity_table_data:
                velocity_data.delete()

            for i in range(table_row):
                for j in range(table_col):
                    data_val = request.POST.get('table-data-' + str(i) + '-' + str(j))
                    VelocitySheetTableData(velocity_equipment=velocity_equipment,
                                           row=i, col=j,
                                           value=data_val).save()

            velocity_equipment.velocity_data = True
            velocity_equipment.velocity_row = table_row
            velocity_equipment.velocity_col = table_col
            velocity_equipment.save()
            return redirect('velocitySheetEquipmentList', my_sheet.id)

    parameters = {
        'velocity_equipment': velocity_equipment,
        'this_sheet_equipment': this_sheet_equipment,
        'equipment_type': equipment_type,
        'actual_fields': actual_fields,
        'sheet_code': sheet_code,
        'my_sheet': my_sheet,
    }
    return render(request, "velocitySheetEquipmentActualData.html", parameters)


@login_required
def velocity_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('velocitySheetHome')
        if request.POST.get("confirm"):
            air_moving_equipments = SheetEquipment.objects.filter(sheet__project=this_sheet.project)
            for air_moving_equipment in air_moving_equipments:
                air_moving_equipment.velocity_data = False
                air_moving_equipment.save()
            this_sheet.delete()
            return redirect('velocitySheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "velocitySheetDelete.html", parameters)

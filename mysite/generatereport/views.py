import math
import os
import re
from itertools import chain
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from .models import *
from .render import Render as PDFRender
from ..sheetcreator.models import *
from django.db.models import Count
from PyPDF2 import PdfMerger, PdfReader

import random
from django.conf import settings
import img2pdf
from PIL import Image
from ..s3_file_manager import S3
import urllib.request as url_request
from ..sheetcreator.render import Render as AMRender
from ..sheetcreator.views import get_pdf_parameters as am_parameters
from ..sheetcreator.views import fetch_sheet_equipment_data as fetch_air_moving_equipment_data
from ..testsheetvav.views import fetch_sheet_equipment_data as fetch_vav_equipment_data
from ..testsheetterminal.views import prepare_pdf_pages as prepare_terminal_pages
from ..testsheetvav.render import Render as VAVRender
from ..testsheetvav.views import get_pdf_parameters as vav_parameters
from ..testsheetvelocity.views import get_pdf_parameters as velocity_parameters
from ..testsheetpump.views import prepare_pump_equipments_data, PumpEquipment

from mysite.equipments.models import DataSheet
from mysite.order.models import Order
from django.conf import settings

from contextlib import contextmanager
from mysite.utils.pdf_to_img import pdf_to_image_bytes
from base64 import b64encode



# Create your views here.

@login_required
def report_sheet_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = ReportSheet.objects.filter(project__project_number__icontains=search).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {
        'sheets': sheets,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "reportSheetList.html", parameters)


@login_required
def report_sheet_add(request):
    form = ReportSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=ReportSheet.objects.values_list('project_id')).order_by('-project_number')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('reportSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                report_sheet = form.save()
                return redirect('reportSheetHome')
    parameters = {
        'form': form,
        'orders': orders,
    }
    return render(request, "reportSheetAdd.html", parameters)


@login_required
def report_sheet_edit(request, sheet_id):
    this_report = get_object_or_404(ReportSheet, id=sheet_id)
    form = ReportSheetForm(request.POST or None, request.FILES or None, instance=this_report)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('reportSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                report_sheet = form.save()
                return redirect('reportSheetHome')
    parameters = {
        'form': form,
    }
    return render(request, "reportSheetEdit.html", parameters)


@login_required
def report_sheet_recreate(request, sheet_id):
    s3 = S3()
    report_sheet = get_object_or_404(ReportSheet, id=sheet_id)
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    report_stamp = LicenseFiles.objects.get(key='ReportStamp').value
    instruction_image = LicenseFiles.objects.get(key='InstructionReport').value
    abbreviation_image = LicenseFiles.objects.get(key='AbbreviationReport').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    parameters = {
        'file_name': ('COVER SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper(),
        'report_sheet': report_sheet,
        'report_stamp': report_stamp,
        'datetime': datetime.datetime.now(),
        'license_owner': license_owner,
        'instruction_image': instruction_image,
        'abbreviation_image': abbreviation_image,
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
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
        'os': system()
    }

    cover_pdf = ReportSheet.create_cover_pdf(parameters)
    parameters['cover_pdf'] = cover_pdf[1]

    parameters['file_name'] = ('REPORT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                           report_sheet.project.project_number)).upper()
    merger = PdfMerger()
    cover = open(cover_pdf[1], "rb")
    merger.append(fileobj=cover)

    if not report_sheet.report_type == 1:
        response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.upload_table_of_content.file)))
        table_of_content_file = open(response[0], "rb")
        merger.append(fileobj=table_of_content_file)

        response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.upload_test_sheets.file)))
        test_sheets = open(response[0], "rb")
        merger.append(fileobj=test_sheets)

        response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.upload_drawing_pdf.file)))
        drawings = open(response[0], "rb")
        merger.append(fileobj=drawings)

    if report_sheet.report_type == 1:

        air_moving_equipments = SheetEquipment.objects.filter(sheet__project=report_sheet.project,
                                                              main_data_entry_completed=True,
                                                              design_data_entry_completed=True,
                                                              actual_data_entry_completed=True)

        exhaust_equipments = air_moving_equipments.filter(equipment_type__name__icontains='EXHAUST')

        air_moving_equipments = air_moving_equipments.exclude(id__in=exhaust_equipments)

        indipendent_vav_equipments = DataSheetEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                       main_data_entry_completed=True,
                                                                       design_data_entry_completed=True,
                                                                       actual_data_entry_completed=True,
                                                                       inherited_from_air_moving__isnull=True)

        pages = []
        request.session['toc_counter'] = 0
        request.session['continues'] = 0
        table_of_content = []

        def toc_line_maker(title, number_of_pages, level, show_page_number=True, underline=False):
            if show_page_number:
                request.session['toc_counter'] = request.session.get('toc_counter') + 1
                table_of_content.append({
                    'name': title,
                    # 'pages': str(request.session['toc_counter']) + ('-' + str(request.session['toc_counter']+number_of_pages+request.session['continues']-1)) if number_of_pages+request.session['continues'] > 1 else str(request.session['toc_counter']),
                    'pages': str(request.session['toc_counter']),
                    'level': level,
                    'underline': underline
                })
                request.session['toc_counter'] = request.session.get('toc_counter') + number_of_pages - 1
            else:
                table_of_content.append({
                    'name': title,
                    'pages': '',
                    'level': level,
                    'underline': underline
                })
            request.session['continues'] = 0

        def add_velocity(air_moving_equipments):
            velocity_pages = []
            number_of_total_pages = 0

            for air_moving_equipment in air_moving_equipments:
                air_moving_equipments = SheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='air mov',
                                                                      sheet__project=report_sheet.project).all()
                velocity_equipments = []
                for velocity_equipment in air_moving_equipment.velocityequipment_set.filter(velocity_data=True):

                    velocity_equipment_obj = {}
                    for velocity_data in velocity_equipment.velocitysheetdata_set.all():
                        velocity_equipment_obj[velocity_data.sheet_field.field_name] = velocity_data.value
                    velocity_equipment_obj['equipment_id'] = velocity_equipment.id
                    velocity_equipments.append(velocity_equipment_obj)

                for velocity_equipment in velocity_equipments:
                    number_of_total_pages = number_of_total_pages + 1
                    velocity_pages.append({
                        'type': 'VELOCITY',
                        'system': 'VELOCITY ' + air_moving_equipment.secd_set.get(
                            key__column_title__icontains='fan no.').value,
                        'rows': [velocity_equipment],
                        'max_row': range(14),
                        'max_col': range(14),
                    })

            if number_of_total_pages > 0:
                toc_line_maker('VELOCITY TRAVERSE TEST SHEET', number_of_total_pages, 1, True, False)

            return velocity_pages

        def add_pump_pages():
            pump_pages = []
            total_pdf_row = 2
            pump_equipments = PumpEquipment.objects.filter(sheet__project=report_sheet.project, design_data_entry_completed=True, actual_data_entry_completed=True).order_by('id')
            pump_equipment_datas = prepare_pump_equipments_data(pump_equipments, total_pdf_row, True)

            total_pages = math.ceil(pump_equipments.count() / total_pdf_row)
            for pump_equipment_data in pump_equipment_datas:
                pump_pages.append({
                    'type': 'PUMP',
                    'system': 'PUMP TEST SHEET',
                    'pump_equipment': pump_equipment_data
                })

            print(len(pump_equipments))
            if len(pump_equipments) > 0:
                toc_line_maker('PUMP TEST SHEET', total_pages, 0, True, False)

            return pump_pages

        def add_rogue_terminal_pages():
            terminal_pages = []
            equipment_in_page = 21
            is_report_pdf = True
            air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                          air_equipment__isnull=True,
                                                                          vav_equipment__isnull=True,
                                                                          type=4).order_by('type', 'other_group', 'outlet_no')


            last_air_equipment_group = 0
            value_list = air_terminal_equipments.values_list('other_group', flat=True).distinct()

            for value in value_list:
                if last_air_equipment_group != value:
                    last_air_equipment_group = value
                    all_air_equipment_terminals = air_terminal_equipments.filter(other_group=value)

                    if len(all_air_equipment_terminals) > 0:
                        terminal_pdf_pages = prepare_terminal_pages(all_air_equipment_terminals, 'OTHER', 0,
                                                                             is_report_pdf,
                                                                             equipment_in_page)
                        toc_line_maker(all_air_equipment_terminals[0].equipment_name, 0, 0, False, True)
                        toc_line_maker('AIR TERMINAL TEST SHEET', len(terminal_pdf_pages), 1, True, False)
                        terminal_pages = terminal_pages + terminal_pdf_pages

            return terminal_pages

        def add_terminal_pages_for_air_moving(air_moving_equipments):
            terminal_pages = []
            number_of_total_pages = 0
            for air_moving_equipment in air_moving_equipments:
                equipment_in_page = 21
                is_report_pdf = True
                air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                              air_equipment__terminal_design_data_entry_completed=True,
                                                                              air_equipment__terminal_actual_data_entry_completed=True,
                                                                              air_equipment=air_moving_equipment) \
                    .order_by('air_equipment__field_order', 'air_equipment_id', 'type', 'outlet_no')

                last_air_equipment_id = 0
                value_list = air_terminal_equipments.values_list('air_equipment_id', flat=True).distinct()
                for value in value_list:
                    if last_air_equipment_id != value:
                        last_air_equipment_id = value
                        all_air_equipment_terminals = air_terminal_equipments.filter(air_equipment_id=value)
                        type_list = all_air_equipment_terminals.values_list('type', flat=True).distinct()
                        group_by_terminal_type = {}
                        for terminal_type in type_list:
                            group_by_terminal_type[terminal_type] = all_air_equipment_terminals.filter(type=terminal_type)

                        done_types = []
                        for terminal_type in type_list:
                            if terminal_type not in done_types:
                                if terminal_type == 1:
                                    adding_supply_pages = prepare_terminal_pages(group_by_terminal_type[1], 'SUPPLY', 1,
                                                                      is_report_pdf,
                                                                      equipment_in_page)
                                    terminal_pages = terminal_pages + adding_supply_pages
                                    number_of_total_pages = number_of_total_pages + len(adding_supply_pages)
                                elif terminal_type == 2:
                                    adding_return_pages = prepare_terminal_pages(group_by_terminal_type[2], 'RETURN', 1,
                                                                                 is_report_pdf,
                                                                                 equipment_in_page)
                                    terminal_pages = terminal_pages + adding_return_pages
                                    number_of_total_pages = number_of_total_pages + len(adding_return_pages)
                                elif terminal_type == 3:
                                    adding_outside_pages = prepare_terminal_pages(group_by_terminal_type[3], 'OUTSIDE', 1,
                                                                                 is_report_pdf,
                                                                                 equipment_in_page)
                                    terminal_pages = terminal_pages + adding_outside_pages
                                    number_of_total_pages = number_of_total_pages + len(adding_outside_pages)
                                done_types.append(terminal_type)


            toc_line_maker('AIR TERMINAL TEST SHEET', number_of_total_pages, 1, True, False)
            return terminal_pages

        def add_vav_pages_using_air_moving(air_moving_equipments):
            vav_pages = []
            is_report_pdf = True
            for air_moving_equipment in air_moving_equipments:
                vav_equipments = DataSheetEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                   inherited_from_air_moving=air_moving_equipment,
                                                                   main_data_entry_completed=True,
                                                                   design_data_entry_completed=True,
                                                                   actual_data_entry_completed=True)

                if len(vav_equipments) > 0:
                    my_sheet = DataSheet.objects.get(test_sheet_type__name__iexact='vav', project=report_sheet.project)

                    equipment_groups = list(map(lambda x: chr(x), range(65, 65 + my_sheet.number_of_equipment_groups)))
                    equipment_in_page = 21
                    last_loop = 0
                    for group in equipment_groups:
                        group_equipments = vav_equipments.filter(equipment_group=group)
                        len_equipments = group_equipments.count()
                        for i in range(math.ceil(len_equipments / equipment_in_page)):
                            last_loop += 1
                            empty_rows = 0
                            page = {
                                'type': 'VAV',
                                'system': 'VAVS ' + air_moving_equipment.secd_set.get(
                                    key__column_title__icontains='fan no.').value,
                                'rows': [],
                                'notes': [],
                                'vavp_available': 0,
                            }
                            for j in range(equipment_in_page):
                                index = i * equipment_in_page + j
                                if index < len_equipments:
                                    page['rows'].append(fetch_vav_equipment_data(group_equipments[index], is_report_pdf))
                                    if group_equipments[index].equipment_type.test_sheet.inheritance:
                                        page['vavp_available'] = 1
                                else:
                                    empty_rows += 1
                            page['empty_rows'] = range(empty_rows)
                            if page['rows']:
                                vav_pages.append(page)

                        if len_equipments > 0:
                            toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', math.ceil(len_equipments / equipment_in_page), 1, True, False)

                        air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                                      vav_equipment__terminal_design_data_entry_completed=True,
                                                                                      vav_equipment__terminal_actual_data_entry_completed=True,
                                                                                      vav_equipment__in=group_equipments.all()) \
                            .order_by('air_equipment__field_order', 'vav_equipment_id', 'type', 'outlet_no')

                        last_vav_equipment_id = 0
                        value_list = air_terminal_equipments.values_list('vav_equipment_id', flat=True).distinct()
                        for value in value_list:
                            if last_vav_equipment_id != value:
                                last_vav_equipment_id = value
                                all_vav_equipment_terminals = air_terminal_equipments.filter(vav_equipment_id=value)

                                if len(all_vav_equipment_terminals) > 0:
                                    vav_terminal_pages = prepare_terminal_pages(all_vav_equipment_terminals, 'SUPPLY', 2,
                                                           is_report_pdf,
                                                           equipment_in_page)
                                    toc_line_maker('AIR TERMINAL TEST SHEET', len(vav_terminal_pages), 2, True, False)
                                    vav_pages = vav_pages + vav_terminal_pages

            return vav_pages

        def add_independent_vav_pages(vav_equipments):
            vav_pages = []
            is_report_pdf = True

            my_sheet = DataSheet.objects.get(test_sheet_type__name__iexact='vav', project=report_sheet.project)

            equipment_groups = list(map(lambda x: chr(x), range(65, 65 + my_sheet.number_of_equipment_groups)))
            equipment_in_page = 21
            last_loop = 0
            for group in equipment_groups:
                group_equipments = vav_equipments.filter(equipment_group=group)
                len_equipments = group_equipments.count()
                for i in range(math.ceil(len_equipments / equipment_in_page)):
                    last_loop += 1
                    empty_rows = 0
                    page = {
                        'type': 'VAV',
                        'system': 'VAVs',
                        'rows': [],
                        'notes': [],
                        'vavp_available': 0,
                    }
                    for j in range(equipment_in_page):
                        index = i * equipment_in_page + j
                        if index < len_equipments:
                            page['rows'].append(fetch_vav_equipment_data(group_equipments[index], is_report_pdf))
                            if group_equipments[index].equipment_type.test_sheet.inheritance:
                                page['vavp_available'] = 1
                        else:
                            empty_rows += 1
                    page['empty_rows'] = range(empty_rows)
                    if page['rows']:
                        vav_pages.append(page)

                if len_equipments > 0:
                    toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', math.ceil(len_equipments / equipment_in_page), 1, True, False)

                air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                              vav_equipment__terminal_design_data_entry_completed=True,
                                                                              vav_equipment__terminal_actual_data_entry_completed=True,
                                                                              vav_equipment__in=group_equipments.all()) \
                    .order_by('vav_equipment__field_order', 'vav_equipment_id', 'type', 'outlet_no')

                if len(air_terminal_equipments) > 0:
                    total_air_equipment_pages = 0
                    vav_air_terminal_equipment_list = []
                    value_list = air_terminal_equipments.values_list('vav_equipment_id', flat=True).distinct()
                    for value in value_list:
                        if value not in vav_air_terminal_equipment_list:
                            all_vav_equipment_terminals = air_terminal_equipments.filter(vav_equipment_id=value)

                            if len(all_vav_equipment_terminals) > 0:
                                air_terminal_pages = prepare_terminal_pages(all_vav_equipment_terminals, 'SUPPLY', 2,
                                                                            is_report_pdf,
                                                                            equipment_in_page)
                                total_air_equipment_pages = total_air_equipment_pages + len(air_terminal_pages)
                                vav_pages = vav_pages + air_terminal_pages
                        vav_air_terminal_equipment_list.append(value)
                    toc_line_maker('AIR TERMINAL TEST SHEET', total_air_equipment_pages, 2, True, False)

            return vav_pages

        while len(air_moving_equipments) > 2:
            current_air_moving_equipments = air_moving_equipments[:2]
            air_moving_equipments = air_moving_equipments[2:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_air_moving_equipments[0].secd_set.get(
                    key__column_title__icontains='fan no.').value + ' & ' + current_air_moving_equipments[
                              1].secd_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(current_air_moving_equipments[0]),
                    fetch_air_moving_equipment_data(current_air_moving_equipments[1]),
                ]
            })
            toc_line_maker(current_air_moving_equipments[0].secd_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + current_air_moving_equipments[
                               1].secd_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving(
                [current_air_moving_equipments[0], current_air_moving_equipments[1]])

            pages = pages + add_velocity([current_air_moving_equipments[0], current_air_moving_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([current_air_moving_equipments[0], current_air_moving_equipments[1]])
        if len(air_moving_equipments) == 2:
            pages.append({
                'type': 'AIRMOVING',
                'system': air_moving_equipments[0].secd_set.get(
                    key__column_title__icontains='fan no.').value + ' & ' + air_moving_equipments[
                              1].secd_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(air_moving_equipments[0]),
                    fetch_air_moving_equipment_data(air_moving_equipments[1]),
                ]
            })
            toc_line_maker(air_moving_equipments[0].secd_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + air_moving_equipments[
                               1].secd_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving([air_moving_equipments[0], air_moving_equipments[1]])

            pages = pages + add_velocity([air_moving_equipments[0], air_moving_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0], air_moving_equipments[1]])
        elif len(air_moving_equipments) == 1:
            pages.append({
                'type': 'AIRMOVING',
                'system': air_moving_equipments[0].secd_set.get(
                    key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(air_moving_equipments[0]),
                ]
            })
            toc_line_maker(air_moving_equipments[0].secd_set.get(
                key__column_title__icontains='fan no.').value,
                           0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving([air_moving_equipments[0]])

            pages = pages + add_velocity([air_moving_equipments[0]])

            pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0]])

        while len(exhaust_equipments) > 2:
            current_exhaust_equipments = exhaust_equipments[:2]
            exhaust_equipments = exhaust_equipments[2:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_exhaust_equipments[0].secd_set.get(key__column_title__icontains='fan no.').value + ' & ' + current_exhaust_equipments[1].secd_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(current_exhaust_equipments[0]),
                    fetch_air_moving_equipment_data(current_exhaust_equipments[1]),
                ]
            })
            toc_line_maker(current_exhaust_equipments[0].secd_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + current_exhaust_equipments[
                               1].secd_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving([current_exhaust_equipments[0], current_exhaust_equipments[1]])

            pages = pages + add_velocity([current_exhaust_equipments[0], current_exhaust_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([current_exhaust_equipments[0], current_exhaust_equipments[1]])
        if len(exhaust_equipments) == 2:
            pages.append({
                'type': 'AIRMOVING',
                'system': exhaust_equipments[0].secd_set.get(
                    key__column_title__icontains='fan no.').value + ' & ' + exhaust_equipments[
                              1].secd_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(exhaust_equipments[0]),
                    fetch_air_moving_equipment_data(exhaust_equipments[1]),
                ]
            })
            toc_line_maker(exhaust_equipments[0].secd_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + exhaust_equipments[
                               1].secd_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving([exhaust_equipments[0], exhaust_equipments[1]])

            pages = pages + add_velocity([exhaust_equipments[0], exhaust_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([exhaust_equipments[0], exhaust_equipments[1]])
        elif len(exhaust_equipments) == 1:
            pages.append({
                'type': 'AIRMOVING',
                'system': exhaust_equipments[0].secd_set.get(
                    key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(exhaust_equipments[0]),
                ]
            })
            toc_line_maker(exhaust_equipments[0].secd_set.get(
                key__column_title__icontains='fan no.').value,
                           0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving([exhaust_equipments[0]])

            pages = pages + add_velocity([exhaust_equipments[0]])

            pages = pages + add_vav_pages_using_air_moving([exhaust_equipments[0]])

        if len(indipendent_vav_equipments) > 0:
            toc_line_maker('VAV\'S', 0, 0, False, True)
            pages = pages + add_independent_vav_pages(indipendent_vav_equipments)

        pages = pages + add_rogue_terminal_pages()

        pages = pages + add_pump_pages()

        if report_sheet.project.colored_drawing_finalize:
            if report_sheet.project.colored_drawing or report_sheet.project.report_colored_drawing:
                toc_line_maker('AS BUILT MECHANICAL PLAN', 1, 0, True, False)

        parameters = {
            'report_sheet': report_sheet,
            'form': {
                'my_sheet': report_sheet,
                'pages': pages,
            },
            'file_name': ('FINAL REPORT {}-{}{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                        report_sheet.project.project_number,'')).upper(),
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
        pdf_name, pdf_path = Render.render_to_file('pdfTemplates/fullTemplate.html', parameters, 'FinalReport')
        full_pdf = open(pdf_path, "rb")

        # Append table of content
        parameters = {
            'table_of_content': table_of_content,
            'report_sheet': report_sheet,
            'file_name': ('TABLE OF CONTENT {}-{}{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                            report_sheet.project.project_number, '')).upper(),
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
        pdf_name, pdf_path = Render.render_to_file('pdfTemplates/tocTemplate.html', parameters, 'TocReport')
        toc_pdf = open(pdf_path, "rb")
        merger.append(fileobj=toc_pdf)

        parameters = {
            'file_name': ('INSTRUMENT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                     report_sheet.project.project_number)).upper(),
            'report_sheet': report_sheet,
            'report_stamp': report_stamp,
            'datetime': datetime.datetime.now(),
            'license_owner': license_owner,
            'instruction_image': instruction_image,
            'abbreviation_image': abbreviation_image,
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
            'MEDIA_URL': settings.MEDIA_URL,
            'STATIC_URL': settings.STATIC_URL,
            'os': system()
        }

        instrument_pdf = ReportSheet.create_report_pdf(parameters)
        parameters['instrument_pdf'] = instrument_pdf[1]
        instrument = open(instrument_pdf[1], "rb")
        merger.append(fileobj=instrument)

        merger.append(fileobj=full_pdf)

        if report_sheet.project.colored_drawing_finalize:
            if report_sheet.project.report_colored_drawing:
                response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.project.report_colored_drawing.file)))
                drawings = open(response[0], "rb")
                merger.append(fileobj=drawings)
            else:
                response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.project.colored_drawing.file)))
                drawings = open(response[0], "rb")
                merger.append(fileobj=drawings)

    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report")):
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report"))
    file_name = ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper() + '.pdf'
    file_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report", file_name)
    s3_path = os.path.join("media/pdfs/report", file_name)
    output = open(file_path, "wb")
    merger.write(output)
    output.close()
    cover.close()
    if not report_sheet.report_type == 1:
        table_of_content_file.close()
        test_sheets.close()
        drawings.close()
    s3.upload_file_to_bucket(file_name=file_path, key=s3_path)

    return JsonResponse({'reload': True}, safe=False)
    # return JsonResponse({'url': MEDIA_URL + 'pdfs/report/' + ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper()}, safe=False)


@login_required
def report_sheet_finalize(request, sheet_id):
    report_sheet = get_object_or_404(ReportSheet, id=sheet_id)
    report_sheet.project.projectprocess.tech_package = True
    report_sheet.project.projectprocess.tech_scheduled = True
    report_sheet.project.projectprocess.job_completed = True
    report_sheet.project.projectprocess.report_out = True
    report_sheet.project.projectprocess.report_out_date = datetime.datetime.now().date()
    report_sheet.project.projectprocess.save()
    report_sheet.project.completion_percentage = 100
    report_sheet.project.pre_demo_completion_percentage = 100
    report_sheet.project.save()
    return redirect('reportSheetHome')


@login_required
def delete_report_sheet(request, sheet_id):
    this_report_sheet = get_object_or_404(ReportSheet, id=sheet_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_report_sheet.upload_drawing_pdf.delete()
            parameters = {
                'file_name': ('REPORT SHEET {}-{}'.format(this_report_sheet.project.proposal.quote.estimate.project.name,
                                                          this_report_sheet.project.project_number)).upper(),
            }
            ReportSheet.delete_report_pdf(parameters)
            this_report_sheet.delete()
        return redirect('reportSheetHome')
    parameters = {'this_report_sheet': this_report_sheet
                  }
    return render(request, "reportSheetDelete.html", parameters)





def get_field_value(field_set, field_name, default=""):
    return field_set.get(field_name, {}).get('value', default)
    
def get_field_note_and_append(field_set, field_name, notes, note_count):
    if field_name in field_set and field_set[field_name].get('note'):
        note_count += 1
        note_marker = str(note_count * "*")
        notes.append(f"{note_marker} {field_set[field_name]['note']}")
        return note_marker, note_count
    return "", note_count

def populate_notes_and_fields(field_names, design_set, actual_set, equipment_data, notes, note_count):
    for field_name, key in field_names.items():
        equipment_data[key] = {
            'design': get_field_value(design_set, field_name),
            'actual': get_field_value(actual_set, field_name)
        }
        design_marker, note_count = get_field_note_and_append(design_set, field_name, notes, note_count)
        actual_marker, note_count = get_field_note_and_append(actual_set, field_name, notes, note_count)
        if design_marker:
            equipment_data[key]['design'] += f" {design_marker}".strip()
        if actual_marker:
            equipment_data[key]['actual'] += f" {actual_marker}".strip()
    return note_count


def fetch_field_data(
        equipment, 
        field_name, 
        default_design_value='', 
        default_actual_value='', 
        is_dict=True, 
        actual_field=None
    ):
    """Fetches design and actual data for a given field name, or returns default values."""
    custom_fields = equipment.form_fields["design"]
    actual_fields = equipment.form_fields["actual"]
    
    design_value = custom_fields.get(field_name, {}).get('value', default_design_value)
    actual_value = actual_fields.get(field_name, {}).get('value', default_actual_value if not is_dict else 'N.M.')
    
    if design_value == '@':
        design_value = ''
    if actual_value == '@':
        actual_value = ''

    if is_dict:
        return {
            'design': design_value if design_value else default_design_value,
            'actual': actual_value if actual_value else default_actual_value
        }
    else:
        return design_value if design_value else default_design_value

def fetch_air_mov_data(equipment):
    """Fetches and returns equipment data."""
    equipment_data = {
        'fan_no': equipment.fan_no,
        'location': equipment.location,
        'area_served': equipment.area_served,
        'manufacturer': equipment.manufacturer.name.upper() if equipment.manufacturer else '',
        'model_no': equipment.model_number,
        'serial_no': fetch_field_data(equipment, 'Serial No.', is_dict=False),
        'total_cfm_fan': fetch_field_data(equipment, 'Total C.F.M. Fan'),
        'air_temp_in_cooling': fetch_field_data(equipment, 'Air Temp. In Cooling'),
        'total_cfm_outlets': fetch_field_data(equipment, 'Total C.F.M. Outlets'),
        'air_temp_out_cooling': fetch_field_data(equipment, 'Air Temp. Out Cooling'),
        'return_air_cfm': fetch_field_data(equipment, 'Return Air C.F.M.'),
        'rh': fetch_field_data(equipment, 'RH %'),
        'outdoor_air_cfm': fetch_field_data(equipment, 'Outdoor Air C.F.M.'),
        'air_temp_in_heating': fetch_field_data(equipment, 'Air Temp. In Heating'),
        'total_sp_ext_sp': fetch_field_data(equipment, 'Total SP (Ext. SP)', default_actual_value='N.S.'),
        'air_temp_out_heating': fetch_field_data(equipment, 'Air Temp. Out Heating'),
        'fan_unit_suction_pressure': fetch_field_data(equipment, 'Fan (Unit) Suction Pressure', default_actual_value='N.S.'),
        'ambient_temp': fetch_field_data(equipment, 'Ambient Temp.'),
        'discharge_pressure_fan_unit': fetch_field_data(equipment, 'Discharge Pressure, Fan / Unit', default_actual_value='N.S.'),
        'oa_damper_poss': fetch_field_data(equipment, 'O.A. Damper Poss.'),
        'fan_rpm': fetch_field_data(equipment, 'Fan R.P.M.', default_design_value='D.D.', default_actual_value='D.D.'),
        'gpm': fetch_field_data(equipment, 'GPM'),
        'hp': fetch_field_data(equipment, 'H.P.', is_dict=False),
        'belt_size': fetch_field_data(equipment, 'Belt Size', is_dict=False, default_design_value='N.A.', default_actual_value='N.A.'),
        'motor_pully': fetch_field_data(equipment, 'Motor Pully', is_dict=False, default_design_value='N.A.', default_actual_value='N.A.'),
        'voltage': fetch_field_data(equipment, 'Voltage'),
        'fan_pully': fetch_field_data(equipment, 'Fan Pully', is_dict=False, default_design_value='N.A.', default_actual_value='N.A.'),
        'phase': fetch_field_data(equipment, 'Phase'),
        'c_to_c': fetch_field_data(equipment, 'C to C', is_dict=False, default_design_value='N.A.', default_actual_value='N.A.'),
        'amperage': fetch_field_data(equipment, 'Amperage'),
        'motor_shaft': fetch_field_data(equipment, 'Motor Shaft', is_dict=False, default_design_value='N.A.', default_actual_value='N.A.'),
        'bhp': fetch_field_data(equipment, 'B.H.P. (Calc.)', default_design_value='N.S.', default_actual_value='N.S.'),
        'fan_shaft': fetch_field_data(equipment, 'Fan Shaft', is_dict=False, default_design_value='N.A.', default_actual_value='N.A.'),
        'frame': fetch_field_data(equipment, 'Frame', default_design_value='N.S.', default_actual_value='N.S.'),
        'vfd_hz': fetch_field_data(equipment, 'VFD / HZ', is_dict=False),
        'sf_code': fetch_field_data(equipment, 'S.F. / Code', default_design_value='N.S.', default_actual_value='N.S.'),
        'filter_size': fetch_field_data(equipment, 'Filter Size', is_dict=False),
        'motor_rpm': fetch_field_data(equipment, 'Motor RPM', default_design_value='D.D.', default_actual_value='D.D.'),
        'filter_model': fetch_field_data(equipment, 'Filter Model', is_dict=False),
        'direct_drive': fetch_field_data(equipment, 'Direct Drive', is_dict=False),
        'belt_drive': fetch_field_data(equipment, 'Belt Drive', is_dict=False),
        'max_speed': fetch_field_data(equipment, 'Max Speed', is_dict=False),
        'med_speed': fetch_field_data(equipment, 'Med Speed', is_dict=False),
        'min_speed': fetch_field_data(equipment, 'Min Speed', is_dict=False),
    }

    # Clean up empty values
    for key, val in equipment_data.items():
        if not val or val == 'None':
            equipment_data[key] = ''

    # Convert all values to upper case
    for key, val in equipment_data.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                equipment_data[key][sub_key] = str(sub_val).upper()
        else:
            equipment_data[key] = str(val).upper()

    # Add notes
    notes = []
    if 'Note' in equipment.form_fields["design"]:
        note_design = equipment.form_fields["design"]['Note']['value']
        notes.append(note_design if note_design else "")
    if 'Note' in equipment.form_fields["actual"]:
        note_actual = equipment.form_fields["actual"]['Note']['value']
        notes.append(note_actual if note_actual else "")
    
    equipment_data['note'] = " ".join(notes).strip()

    return equipment_data

def fetch_vav_data(this_sheet_equipment):
    design_field_set = this_sheet_equipment.form_fields["design"]
    actual_field_set = this_sheet_equipment.form_fields["actual"]

    equipment_data = {
        'inherit': this_sheet_equipment.equipment_type.test_sheet.inheritance,
        'address': get_field_value(design_field_set, "Address"),
        'code': this_sheet_equipment.code,
        'type': get_field_value(design_field_set, "Type"),
        'size_kw': get_field_value(design_field_set, "Size / KW"),
        'fan': get_field_value(design_field_set, "Fan %"),
        'fan_cfm': get_field_value(design_field_set, "Fan CFM"),
        'kf': get_field_value(actual_field_set, "K.F."),
        'min_fan_cfm': get_field_value(actual_field_set, "Min. / Fan CFM"),
        'model_number': this_sheet_equipment.model_number,
        'hp': get_field_value(actual_field_set, "H.P."),
        'make': this_sheet_equipment.manufacturer,
        'fan_volt': get_field_value(actual_field_set, "Fan volt"),
        'fan_amp': get_field_value(actual_field_set, "Fan Amp"),
        't_in': get_field_value(actual_field_set, "T In"),
        'fan_va': get_field_value(actual_field_set, "Fan V / A"),
        't_out': get_field_value(actual_field_set, "T Out"),
        'max_cfm': {
            'design': get_field_value(design_field_set, "Max. CFM"),
            'actual': get_field_value(actual_field_set, "Max. CFM")
        },
        'min_cfm': {
            'design': get_field_value(design_field_set, "Min. CFM"),
            'actual': get_field_value(actual_field_set, "Min. CFM")
        },
        "heat_va": get_field_value(actual_field_set, "Heat V / A"),
        "heat_va_actual": get_field_value(actual_field_set, "Heat V / A Actual"),
        "note": "",
    }

    if not equipment_data['fan_cfm']:
        equipment_data['fan_cfm'] = "----"
    if not equipment_data['kf']:
        equipment_data['kf'] = "----"
    if not equipment_data['min_fan_cfm']:
        equipment_data['min_fan_cfm'] = "----"
    if not equipment_data['max_cfm']['design']:
        equipment_data['max_cfm']['design'] = "----"
    if not equipment_data['max_cfm']['actual']:
        equipment_data['max_cfm']['actual'] = "----"

    notes = []
    eq_types = {
        'HW': 'Hot Water',
        'RH': 'Reheat',
        'CO': 'Cooling Only',
        'FPS': 'Fan Powered Series',
        'FPP': 'Fan Powered Parallel',
    }
    if equipment_data['type'] in eq_types:
        tmp = f"{equipment_data['type']}: {eq_types[equipment_data['type']]}".strip()
        notes.append(tmp)
    note_count = 0

    note_fields = {
        'Address': 'address',
        'Code': 'code',
        'Type': 'type',
        'Size / KW': 'size_kw',
        'Fan %': 'fan',
        'Fan CFM': 'fan_cfm',
        'K.F.': 'kf',
        'Min. / Fan CFM': 'min_fan_cfm',
        'Fan volt': 'fan_volt',
        'Fan Amp': 'fan_amp',
        'T In': 't_in',
        'Fan V / A': 'fan_va',
        'T Out': 't_out',
        "Min. CFM": 'min_cfm',
        "Max. CFM": 'max_cfm',
        "Heat V / A": 'heat_va',
    }

    for field_name, key in note_fields.items():
        this_note_design = design_field_set.get(field_name, {}).get('note', '')
        this_note_actual = actual_field_set.get(field_name, {}).get('note', '')
        if this_note_design:
            note_count += 1
            note_marker = str(note_count * "*")
            notes.append(f"{note_marker} {this_note_design}")
            equipment_data[key] += f" {note_marker}"
        if this_note_actual:
            note_count += 1
            note_marker = str(note_count * "*")
            notes.append(f"{note_marker} {this_note_actual}")
            equipment_data[key] += f" {note_marker}"

    if notes:
        notes = [note for note in notes if note]
        notes = list(set(notes))
        equipment_data['note'] = " | ".join(notes)

    # Clean up any fields that are empty or None
    for key, val in equipment_data.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                equipment_data[key][sub_key] = sub_val if sub_val else ''
        else:
            equipment_data[key] = val if val else ''

    # Convert all values to upper case
    for key, val in equipment_data.items():
        if key == 'note':
            continue
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                equipment_data[key][sub_key] = str(sub_val).upper()
        else:
            equipment_data[key] = str(val).upper()

    return equipment_data

def fetch_terminal_data(terminals, _type):

    def map_type(_type):
        return {
            1: 'SUPPLY',
            2: 'RETURN',
            3: 'OTHER',
            4: 'EXHAUST'
        }.get(_type, '')

    def get_field_value(field_set, field_name, default=""):
        return field_set.get(field_name, {}).get('value', default)

    def process_terminal_data(terminal, _type):
        design_field_set = terminal.form_fields["design"]
        actual_field_set = terminal.form_fields["actual"]

        equipment_data = {
            'room_no': get_field_value(design_field_set, "Room No."),
            'outlet_no': terminal.outlet_no,
            'code': get_field_value(design_field_set, "Code"),
            'size': get_field_value(design_field_set, "Size"),
            'ak_factor': get_field_value(design_field_set, "AK Factor"),
            'fpm': {
                'design': get_field_value(design_field_set, "FPM", "*"),
                'initial': get_field_value(actual_field_set, "Initial FPM", "*"),
                'final': get_field_value(actual_field_set, "Final FPM", "*")
            },
            'cfm': {
                'design': get_field_value(design_field_set, "CFM"),
                'initial': get_field_value(actual_field_set, "Initial CFM"),
                'final': get_field_value(actual_field_set, "Final CFM")
            },
            'note': "",
            'title': terminal.fan_no,
            'type': _type,
        }
        # for fpm if number or float round to int
        if equipment_data['fpm']['design'] and equipment_data['fpm']['design'] != "*":
            equipment_data['fpm']['design'] = int(float(equipment_data['fpm']['design']))
        if equipment_data['fpm']['initial'] and equipment_data['fpm']['initial'] != "*":
            equipment_data['fpm']['initial'] = int(float(equipment_data['fpm']['initial']))
        if equipment_data['fpm']['final'] and equipment_data['fpm']['final'] != "*":
            equipment_data['fpm']['final'] = int(float(equipment_data['fpm']['final']))
        
        # Convert all values to upper case
        for key, val in equipment_data.items():
            if isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    equipment_data[key][sub_key] = str(sub_val).upper() if sub_val else ''
            else:
                equipment_data[key] = str(val).upper() if val else ''

        return equipment_data

    def calculate_totals(equipments):
        total_cfm_design = sum(int(e['cfm']['design']) for e in equipments if e['cfm']['design'] and e['cfm']['design'] != "*")
        total_cfm_initial = sum(int(e['cfm']['initial']) for e in equipments if e['cfm']['initial'] and e['cfm']['initial'] != "*")
        total_cfm_final = sum(int(e['cfm']['final']) for e in equipments if e['cfm']['final'] and e['cfm']['final'] != "*")
        if total_cfm_design == 0:
            total_cfm_design = ""
        if total_cfm_initial == 0:
            total_cfm_initial = ""
        if total_cfm_final == 0:
            total_cfm_final = ""
        return total_cfm_design, total_cfm_initial, total_cfm_final

    def create_page(terminals, equipments, _type, total_cfm_design, total_cfm_initial, total_cfm_final):
        if terminals[0].parent:
            this_title = terminals[0].parent.name or terminals[0].parent.fan_no
        else:
            this_title = "OTHER TERMINAL"
        page = {
            'type': 'TERMINAL',
            'eq_name': "Terminal",
            'system': this_title,
            'rows': equipments,
            'title': f"{this_title} {_type}",
            'total': {
                'footer': f'TOTAL {_type} {this_title}',
                'cfm_design': total_cfm_design,
                'cfm_initial': total_cfm_initial,
                'cfm_final': total_cfm_final,
            }
        }

        if (terminals[0].parent) and 'V.A.V' in (terminals[0].parent.equipment_type.test_sheet.name):
            design_code = terminals[0].parent.code
            page['system'] = "Existing Supply".upper()
            page['title'] = f"{design_code} {_type}".upper()
            page['total']['footer'] = f'TOTAL {_type} {design_code}'.upper()

        # Add empty rows to fill the page
        equipment_in_page = 18  # 21 total rows - 3 header rows
        page['empty_rows'] = [{} for _ in range(equipment_in_page - len(equipments))]

        return page

    _type = map_type(_type)
    equipments = [process_terminal_data(terminal, _type) for terminal in terminals]

    total_cfm_design, total_cfm_initial, total_cfm_final = calculate_totals(equipments)

    page = create_page(terminals, equipments, _type, total_cfm_design, total_cfm_initial, total_cfm_final)
    
    return page

def fetch_pump_data(pumps):
    data = []
    for p in pumps:
        design_field_set = p.form_fields["design"]
        actual_field_set = p.form_fields["actual"]

        equipment_data = {
            'pump_no': p.model_number,
            'manufacturer': p.manufacturer.name.upper() if p.manufacturer else '',
            'serial_no': get_field_value(actual_field_set, "Serial No."),
            'model_size': f"{p.model_number} / {get_field_value(design_field_set, 'Size')}",
            'impeller_rpm': f"{get_field_value(design_field_set, 'Impeller')} / {get_field_value(design_field_set, 'RPM')}",
            'maxwk_mfgdate': f"{get_field_value(design_field_set, 'Max. Wk. Pr.')} / {get_field_value(design_field_set, 'Mfg. Date')}",
            'design_gpm': get_field_value(design_field_set, 'Design GPM'),
            'design_ft': get_field_value(design_field_set, 'Design FT'),
            'design_bhp': get_field_value(actual_field_set, 'Design BHP'),
            'actual_gpm': get_field_value(actual_field_set, 'Actual GPM'),
            'actual_ft': get_field_value(actual_field_set, 'Actual FT'),
            'actual_bhp': get_field_value(actual_field_set, 'Actual BHP'),
            'discharge_gpm': get_field_value(actual_field_set, 'Discharge GPM'),
            'discharge_ft': get_field_value(actual_field_set, 'Discharge FT'),
            'discharge_bhp': get_field_value(actual_field_set, 'Discharge BHP'),
            'suction_gpm': get_field_value(actual_field_set, 'Suction GPM'),
            'suction_ft': get_field_value(actual_field_set, 'Suction FT'),
            'suction_bhp': get_field_value(actual_field_set, 'Suction BHP'),
            'discharge_suction': get_field_value(actual_field_set, 'Discharge / Suction'),
            'motor_mfg': get_field_value(actual_field_set, 'Motor Mfg.'),
            'hp_frame': f"{get_field_value(design_field_set, 'HP')} / {get_field_value(design_field_set, 'Frame')}",
            'sf_code': f"{get_field_value(design_field_set, 'S.F.')} / {get_field_value(design_field_set, 'Code')}",
            'rpm_phase_hz': f"{get_field_value(design_field_set, 'RPM')} / {get_field_value(design_field_set, 'Phase')} / {get_field_value(design_field_set, 'HZ')}",
            'amps_design': get_field_value(design_field_set, 'Amps'),
            'amps_actual': get_field_value(actual_field_set, 'Amps'),
            'volts_design': get_field_value(design_field_set, 'Volts'),
            'volts_actual': get_field_value(actual_field_set, 'Volts'),
            'note': "",
        }

        notes = []
        note_count = 0
        data.append(equipment_data)
    return data

def fetch_velocity_data(equipment):
    design_field_set = equipment.form_fields["design"]
    actual_field_set = equipment.form_fields["actual"]

    equipment_data = {
        'fan_no': design_field_set.get('Fan No.', {}).get('value', ''),
        'design_cfm': design_field_set.get('Design C.F.M.', {}).get('value', ''),
        'duct_size': actual_field_set.get('Duct Size', {}).get('value', ''),
        'duct_area': actual_field_set.get('Duct Area', {}).get('value', ''),
        'reqd_vel': actual_field_set.get('Req. Vel', {}).get('value', ''),
        'traverse_location': actual_field_set.get('Traverse Location', {}).get('value', ''),
        'actual_cfm': {
            'initial': actual_field_set.get('Actual CFM. Initial', {}).get('value', ''),
            'final': actual_field_set.get('Actual CFM. Final', {}).get('value', ''),
        },
        'duct_static': {
            'initial': actual_field_set.get('Duct Static Initial', {}).get('value', ''),
            'final': actual_field_set.get('Duct Static Final', {}).get('value', ''),
        },
        'actual_vel': {
            'initial': actual_field_set.get('Actual Vel Initial', {}).get('value', ''),
            'final': actual_field_set.get('Actual Vel Final', {}).get('value', ''),
        },
        'note': "",
    }
    # Convert all values to upper case
    for key, val in equipment_data.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                equipment_data[key][sub_key] = str(sub_val).upper() if sub_val else ''
        else:
            equipment_data[key] = str(val).upper() if val else ''
    
    notes = []
    note_count = 0
    note_count = populate_notes_and_fields({
        'Note': 'note'
    }, design_field_set, actual_field_set, equipment_data, notes, note_count)
    equipment_data['note'] = " | ".join(notes)

    return equipment_data

def fetch_flow_measuring_data(equipments):
    data = []
    total_design_gpm = 0
    total_final_gpm = 0
    total_title = "TOTAL FLOW MEASURING STATION"
    for e in equipments:
        design_field_set = e.form_fields["design"]
        actual_field_set = e.form_fields["actual"]

        equipment_data = {
            'br_no': actual_field_set.get('Br No.', {}).get('value', ''),
            'fmf_no': actual_field_set.get('FMF No.', {}).get('value', ''),
            'location': actual_field_set.get('Location', {}).get('value', ''),
            'unit_number': e.code,
            'model_number': e.model_number,
            'design': {
                'set_pd': actual_field_set.get('Set / P.D.', {}).get('value', ''),
                'gpm': design_field_set.get('Design G.P.M.', {}).get('value', ''),
            },
            'initial_test': {
                'set_pd': actual_field_set.get('Initial Test Set / P.D.', {}).get('value', ''),
                'gpm': actual_field_set.get('Initial Test G.P.M.', {}).get('value', ''),
            },
            'final': {
                'set_pd': actual_field_set.get('Final Set / P.D.', {}).get('value', ''),
                'gpm': actual_field_set.get('Final G.P.M.', {}).get('value', ''),
            },
            'note': "",
        }
        # iterate and set '' for None
        for key, val in equipment_data.items():
            if isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    equipment_data[key][sub_key] = sub_val if sub_val else ''
            else:
                equipment_data[key] = val if val else ''

        notes = []
        note_count = 0
        note_count = populate_notes_and_fields({
            'Note': 'note'
        }, design_field_set, actual_field_set, equipment_data, notes, note_count)
        equipment_data['note'] = " | ".join(notes)

        data.append(equipment_data)
        total_design_gpm += int(equipment_data['design']['gpm']) if equipment_data['design']['gpm'] else 0
        total_final_gpm += int(equipment_data['final']['gpm']) if equipment_data['final']['gpm'] else 0
    return {
        'data': data, 
        'total_design_gpm': total_design_gpm, 
        'total_final_gpm': total_final_gpm, 
        'total_title': total_title
    }
    
@login_required
def report_sheet_recreate_call(
    request, 
    order_id,
    report_type,
    start_date,
    end_date,
    report_date,
    revised_date
):
    s3 = S3()
    order = get_object_or_404(Order, id=order_id)
    if revised_date:
        # report_sheet = ReportSheet.objects.get_or_create(
        #     project=order, 
        #     report_type=1,
        #     report_date=report_date,
        #     revised_date=revised_date
        # )[0]
        report_sheet = ReportSheet.objects.create(
            project=order, 
            report_type=1,
            report_date=report_date,
            revised_date=revised_date
        )
    else:
        # report_sheet = ReportSheet.objects.get_or_create(
        #     project=order, 
        #     report_type=1,
        #     report_date=report_date
        # )[0]
        report_sheet = ReportSheet.objects.create(
            project=order, 
            report_type=1,
            report_date=report_date
        )
    if start_date:
        order.start_date = start_date
    if end_date:
        order.end_date = end_date
    if start_date or end_date:
        order.save()

    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    report_stamp = LicenseFiles.objects.get(key='ReportStamp').value
    instruction_image = LicenseFiles.objects.get(key='InstructionReport').value
    abbreviation_image = LicenseFiles.objects.get(key='AbbreviationReport').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    parameters = {
        'file_name': ('COVER SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper(),
        'report_sheet': report_sheet,
        'report_stamp': report_stamp,
        'datetime': datetime.datetime.now(),
        'license_owner': license_owner,
        'instruction_image': instruction_image,
        'abbreviation_image': abbreviation_image,
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
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
        'os': system(),
    }

    cover_pdf = ReportSheet.create_cover_pdf(parameters)
    parameters['cover_pdf'] = cover_pdf[1]

    parameters['file_name'] = ('REPORT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                           report_sheet.project.project_number)).upper()
    merger = PdfMerger()
    cover = open(cover_pdf[1], "rb")
    merger.append(fileobj=cover)

    if not report_sheet.report_type == 1:
        response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.upload_table_of_content.file)))
        table_of_content_file = open(response[0], "rb")
        merger.append(fileobj=table_of_content_file)

        response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.upload_test_sheets.file)))
        test_sheets = open(response[0], "rb")
        merger.append(fileobj=test_sheets)

        response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.upload_drawing_pdf.file)))
        drawings = open(response[0], "rb")
        merger.append(fileobj=drawings)

    if report_sheet.report_type == 1:
        datasheets = DataSheet.objects.filter(project=report_sheet.project)
        air_moving_equipments = datasheets.filter(equipment_type__test_sheet__name__iexact='Air Moving').all()
        # indipendent_vav_equipments = datasheets.exclude(
        #     equipment_type__test_sheet__name__iexact='Air Moving').exclude(
        #     equipment_type__test_sheet__name__iexact='Air Terminal'
        # ).all()
        indipendent_vav_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='V.A.V').all()
        velocity_traverse_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='Velocity Traverse').all()

        pages = []
        request.session['toc_counter'] = 0
        request.session['continues'] = 0
        table_of_content = []

        def toc_line_maker(title, number_of_pages, level, show_page_number=True, underline=False):
            if show_page_number:
                request.session['toc_counter'] = request.session.get('toc_counter') + 1
                table_of_content.append({
                    'name': title,
                    # 'pages': str(request.session['toc_counter']) + ('-' + str(request.session['toc_counter']+number_of_pages+request.session['continues']-1)) if number_of_pages+request.session['continues'] > 1 else str(request.session['toc_counter']),
                    'pages': str(request.session['toc_counter']),
                    'level': level,
                    'underline': underline
                })
                request.session['toc_counter'] = request.session.get('toc_counter') + number_of_pages - 1
            else:
                table_of_content.append({
                    'name': title,
                    'pages': '',
                    'level': level,
                    'underline': underline
                })
            request.session['continues'] = 0

        def add_rogue_terminal_pages():
            terminal_pages = []
            equipment_in_page = 21
            is_report_pdf = True
            air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                          air_equipment__isnull=True,
                                                                          vav_equipment__isnull=True,
                                                                          type=4).order_by('type', 'other_group', 'outlet_no')


            last_air_equipment_group = 0
            value_list = air_terminal_equipments.values_list('other_group', flat=True).distinct()

            for value in value_list:
                if last_air_equipment_group != value:
                    last_air_equipment_group = value
                    all_air_equipment_terminals = air_terminal_equipments.filter(other_group=value)

                    if len(all_air_equipment_terminals) > 0:
                        terminal_pdf_pages = prepare_terminal_pages(all_air_equipment_terminals, 'OTHER', 0,
                                                                             is_report_pdf,
                                                                             equipment_in_page)
                        toc_line_maker(all_air_equipment_terminals[0].equipment_name, 0, 0, False, True)
                        toc_line_maker('AIR TERMINAL TEST SHEET', len(terminal_pdf_pages), 1, True, False)
                        terminal_pages = terminal_pages + terminal_pdf_pages

            return terminal_pages

        def add_terminal_pages_for_air_moving(air_moving_equipment):
            terminal_pages = []
            equipment_in_page = 21

            air_terminal_equipments = DataSheet.objects.filter(project=report_sheet.project, parent=air_moving_equipment.id).order_by('_type', 'outlet_no')
            if len(air_terminal_equipments) > 0:

                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=1), 1
                )
                terminal_pages.append(air_terminal_pages)

                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=2), 2
                )
                terminal_pages.append(air_terminal_pages)
                
                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=3), 3
                )
                terminal_pages.append(air_terminal_pages)

                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=4), 4
                )
                terminal_pages.append(air_terminal_pages)
            
            terminal_pages = [page for page in terminal_pages if page]
            if terminal_pages:
                terminal_pages = terminal_pages[0]

            return terminal_pages

        def add_vav_pages_using_air_moving(air_moving_equipments):
            vav_pages = []
            is_report_pdf = True
            for air_moving_equipment in air_moving_equipments:
                vav_equipments = DataSheetEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                   inherited_from_air_moving=air_moving_equipment,
                                                                   main_data_entry_completed=True,
                                                                   design_data_entry_completed=True,
                                                                   actual_data_entry_completed=True)

                if len(vav_equipments) > 0:
                    my_sheet = DataSheet.objects.get(test_sheet_type__name__iexact='vav', project=report_sheet.project)

                    equipment_groups = list(map(lambda x: chr(x), range(65, 65 + my_sheet.number_of_equipment_groups)))
                    equipment_in_page = 21
                    last_loop = 0
                    for group in equipment_groups:
                        group_equipments = vav_equipments.filter(equipment_group=group)
                        len_equipments = group_equipments.count()
                        for i in range(math.ceil(len_equipments / equipment_in_page)):
                            last_loop += 1
                            empty_rows = 0
                            page = {
                                'type': 'VAV',
                                'system': 'VAVS ' + air_moving_equipment.secd_set.get(
                                    key__column_title__icontains='fan no.').value,
                                'rows': [],
                                'notes': [],
                                'vavp_available': 0,
                            }
                            for j in range(equipment_in_page):
                                index = i * equipment_in_page + j
                                if index < len_equipments:
                                    page['rows'].append(fetch_vav_equipment_data(group_equipments[index], is_report_pdf))
                                    if group_equipments[index].equipment_type.test_sheet.inheritance:
                                        page['vavp_available'] = 1
                                else:
                                    empty_rows += 1
                            page['empty_rows'] = range(empty_rows)
                            if page['rows']:
                                vav_pages.append(page)

                        if len_equipments > 0:
                            toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', math.ceil(len_equipments / equipment_in_page), 1, True, False)

                        air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                                      vav_equipment__terminal_design_data_entry_completed=True,
                                                                                      vav_equipment__terminal_actual_data_entry_completed=True,
                                                                                      vav_equipment__in=group_equipments.all()) \
                            .order_by('air_equipment__field_order', 'vav_equipment_id', 'type', 'outlet_no')

                        last_vav_equipment_id = 0
                        value_list = air_terminal_equipments.values_list('vav_equipment_id', flat=True).distinct()
                        for value in value_list:
                            if last_vav_equipment_id != value:
                                last_vav_equipment_id = value
                                all_vav_equipment_terminals = air_terminal_equipments.filter(vav_equipment_id=value)

                                if len(all_vav_equipment_terminals) > 0:
                                    vav_terminal_pages = prepare_terminal_pages(all_vav_equipment_terminals, 'SUPPLY', 2,
                                                           is_report_pdf,
                                                           equipment_in_page)
                                    toc_line_maker('AIR TERMINAL TEST SHEET', len(vav_terminal_pages), 2, True, False)
                                    vav_pages = vav_pages + vav_terminal_pages

            return vav_pages

        def add_independent_vav_pages(vav_equipments):
            vav_pages = []

            equipment_in_page = 10  # Number of equipments per page
            total_equipments = vav_equipments.count()

            vav_eqs = []
            for eq in vav_equipments:
                vav_eqs.append(fetch_vav_data(eq))

            # Create VAV pages with 8 equipments each
            for i in range(math.ceil(total_equipments / equipment_in_page)):
                rows = vav_eqs[i * equipment_in_page: (i + 1) * equipment_in_page]
                
                # Only proceed if there are actual rows
                if rows:
                    empty_rows = [None] * (equipment_in_page - len(rows))
                    
                    page = {
                        'type': 'VAV',
                        'system': 'VAVs',
                        'rows': rows + empty_rows,  # Filling the remaining rows with `None` to indicate emptiness
                        'notes': [],
                        'vavp_available': 0,
                        'empty_rows': empty_rows
                    }

                    # Check if any equipment on the page has inheritance, set `vavp_available` if true
                    for equipment_data in rows:  # Only check actual rows, not the empty placeholders
                        if equipment_data.get('inheritance', False):  # Assuming 'inheritance' key in equipment data
                            page['vavp_available'] = 1
                            break

                    vav_pages.append(page)

            # Add TOC line for the VAV schedule only if there are any pages
            if vav_pages:
                toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', len(vav_pages), 1, True, False)

            # Now handle air terminal equipment pages
            air_terminal_equipments = DataSheet.objects.filter(
                project=report_sheet.project,
                parent__in=vav_equipments,
            ).order_by('id', '_type', 'outlet_no')

            if len(air_terminal_equipments) > 0:
                air_terminal_pages = fetch_terminal_data(air_terminal_equipments, 1)
                vav_pages.extend(air_terminal_pages)
                toc_line_maker('AIR TERMINAL TEST SHEET', len(air_terminal_pages), 2, True, False)

            return vav_pages

        def add_velocity_traverse_pages(velocity_traverse_equipments):
            pages = []
            for eq in velocity_traverse_equipments:
                rows = fetch_velocity_data(eq)
                page = {
                    'type': 'VELOCITY',
                    'system': 'VELOCITY TRAVERSE',
                    'rows': rows,
                }
                toc_line_maker('VELOCITY TRAVERSE TEST SHEET', 1, 1, True, False)
                pages.append(page)
            return pages

        while len(air_moving_equipments):
            current_air_moving_equipments = air_moving_equipments[0]
            air_moving_equipments = air_moving_equipments[1:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_air_moving_equipments.fan_no,
                'rows': [
                    fetch_air_mov_data(current_air_moving_equipments),
                ]
            })
            toc_line_maker(current_air_moving_equipments.fan_no, 0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            terminals = add_terminal_pages_for_air_moving(current_air_moving_equipments)
            if terminals:
                toc_line_maker('AIR TERMINAL TEST SHEET', len(terminals), 2, True, False)
                pages.extend(terminals)
            # pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0]])

        if len(indipendent_vav_equipments) > 0:
            toc_line_maker('VAV\'S', 0, 0, False, True)
            pages = pages + add_independent_vav_pages(indipendent_vav_equipments)

        if len(velocity_traverse_equipments) > 0:
            toc_line_maker('VELOCITY TRAVERSE', 0, 0, False, True)
            pages = pages + add_velocity_traverse_pages(velocity_traverse_equipments)

        # pages = pages + add_rogue_terminal_pages()

        # attachment
        for ds in datasheets:
            if ds.attach:
                title = ds.name
                if ds.equipment_type.test_sheet.name == 'Air Moving':
                    title = ds.fan_no
                elif 'V.A.V' in ds.equipment_type.test_sheet.name:
                    title = ds.code

                url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(ds.attach.file)
                url = url.replace("/media///app/", "")
                response = url_request.urlretrieve(url)
                attach = open(response[0], "rb")
                tmp_reader = PdfReader(attach)
                toc_line_maker(f"{ds.attach_type} ({title})", len(tmp_reader.pages), 1, True, False)

        if report_sheet.project.colored_drawing or report_sheet.project.report_colored_drawing:
            toc_line_maker('AS BUILT MECHANICAL PLAN', 1, 1, True, False)

        parameters = {
            'report_sheet': report_sheet,
            'form': {
                'my_sheet': report_sheet,
                'pages': pages,
            },
            'file_name': ('FINAL REPORT {}-{}{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                        report_sheet.project.project_number,'')).upper(),
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
        pdf_name, pdf_path = Render.render_to_file('pdfTemplates/fullTemplate_2.html', parameters, 'FinalReport')
        full_pdf = open(pdf_path, "rb")

        # Append table of content
        parameters = {
            'table_of_content': table_of_content,
            'report_sheet': report_sheet,
            'file_name': ('TABLE OF CONTENT {}-{}{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                            report_sheet.project.project_number, '')).upper(),
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
        pdf_name, pdf_path = Render.render_to_file('pdfTemplates/tocTemplate_2.html', parameters, 'TocReport')
        toc_pdf = open(pdf_path, "rb")
        merger.append(fileobj=toc_pdf)

        parameters = {
            'file_name': ('INSTRUMENT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                     report_sheet.project.project_number)).upper(),
            'report_sheet': report_sheet,
            'report_stamp': report_stamp,
            'datetime': datetime.datetime.now(),
            'license_owner': license_owner,
            'instruction_image': instruction_image,
            'abbreviation_image': abbreviation_image,
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
            'MEDIA_URL': settings.MEDIA_URL,
            'STATIC_URL': settings.STATIC_URL,
            'os': system()
        }

        instrument_pdf = ReportSheet.create_report_pdf(parameters)
        parameters['instrument_pdf'] = instrument_pdf[1]
        instrument = open(instrument_pdf[1], "rb")
        merger.append(fileobj=instrument)
        merger.append(fileobj=full_pdf)

        # append attaches
        for ds in datasheets:
            if ds.attach:
                url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(ds.attach.file)
                url = url.replace("/media///app/", "")
                response = url_request.urlretrieve(url)
                attach = open(response[0], "rb")
                merger.append(fileobj=attach)

        if report_sheet.project.report_colored_drawing:
            # response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.project.report_colored_drawing.file)))
            
            url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(report_sheet.project.report_colored_drawing.file)
            url = url.replace("/media///app/", "")
            print("===" * 15)
            print(url)
            response = url_request.urlretrieve(url)
            drawings = open(response[0], "rb")
            merger.append(fileobj=drawings)
        else:
            # response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.project.colored_drawing.file)))
            url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(report_sheet.project.colored_drawing.file)
            url = url.replace("/media///app/", "")
            print("===" * 15)
            print(url)
            response = url_request.urlretrieve()
            drawings = open(response[0], "rb")
            merger.append(fileobj=drawings)

    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report")):
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report"))
    file_name = ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper() + '.pdf'
    file_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report", file_name)
    s3_path = os.path.join("media/pdfs/report", file_name)
    output = open(file_path, "wb")
    merger.write(output)
    output.close()
    cover.close()
    if not report_sheet.report_type == 1:
        table_of_content_file.close()
        test_sheets.close()
        drawings.close()
    s3.upload_file_to_bucket(file_name=file_path, key=s3_path)

    # return JsonResponse({'reload': True}, safe=False)
    # return JsonResponse({'url': settings.MEDIA_URL + 'pdfs/report/' + ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper()}, safe=False)
    # s3.get_bucket_object(os.path.join("media/pdfs/report", final_pdf_name))
    return s3.get_bucket_object(s3_path)


@login_required
def report_sheet_show(
    request, 
    order_id,
):
    order = get_object_or_404(Order, id=order_id)
    toc = []

    context = {
        'order_id': order_id,
        'report_type': request.GET.get('report_type'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'report_date': request.GET.get('report_date'),
        'revised_date': request.GET.get('revised_date'),

        'project': order.proposal.quote.estimate.project.name.upper(),
        'project_no': order.project_number.upper(),
        'client': order.proposal.quote.estimate.customer.company.name.upper(),

        'header': {
            'text': LicenseInfo.objects.get(key='PDFHeaderText').value
        },
        'footer': {
            'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
            'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
            'owner_tel': LicenseInfo.objects.get(key='OwnerTel').value,
            'owner_fax': LicenseInfo.objects.get(key='OwnerFax').value,
            'owner_web': LicenseInfo.objects.get(key='OwnerWeb').value,
            'owner_mail': LicenseInfo.objects.get(key='OwnerMail').value,
        },
        'cover': {
            'project': order.proposal.quote.estimate.project.name.upper(),
            'location': "",
            'contractor': order.proposal.quote.estimate.customer.company.name.upper(),
            'architect': order.architect_name.company.name.upper() if order.architect_name else "N.S.",
            'engineer': order.proposal.quote.estimate.engineer.company.name.upper() if order.proposal.quote.estimate.engineer else "N.S.",
            'project_no': order.project_number.upper(),
        },
        'toc': [],
        'general_info': {
            'notes_and_comments': order.general_notes_and_comments,
            'guaranty': {
                'owner': LicenseInfo.objects.get(key='OwnerName').value,
                'company': LicenseInfo.objects.get(key='CompanyName').value,
                'address': "",
                'address2': "",
                'eng_firm': order.proposal.quote.estimate.engineer.company.name.upper(),
                'eng_firm_address': "",
                'eng_firm_address2': "",
            }
        },
        'pages': [],
    }
    if order.proposal.quote.estimate.project.address_line_1:
        context['cover']['location'] += order.proposal.quote.estimate.project.address_line_1.upper()
    if order.proposal.quote.estimate.project.address_line_2:
        context['cover']['location'] += ", " + order.proposal.quote.estimate.project.address_line_2.upper()
    if order.proposal.quote.estimate.project.city:
        context['cover']['location'] += ", " + order.proposal.quote.estimate.project.city.upper()
    if order.proposal.quote.estimate.project.state:
        context['cover']['location'] += ", " + order.proposal.quote.estimate.project.state.upper()
    if order.proposal.quote.estimate.project.zip:
        context['cover']['location'] += ", " + order.proposal.quote.estimate.project.zip.upper()
    if context['cover']['engineer'] == "UNKNOWN":
        context['cover']['engineer'] = "N.S."
    # guarenty address
    if order.proposal.quote.estimate.project.address_line_1:
        context['general_info']['guaranty']['address'] = order.proposal.quote.estimate.project.address_line_1
    if order.proposal.quote.estimate.project.address_line_2:
        context['general_info']['guaranty']['address'] += ", " + order.proposal.quote.estimate.project.address_line_2
    if order.proposal.quote.estimate.project.city:
        context['general_info']['guaranty']['address2'] = order.proposal.quote.estimate.project.city
    if order.proposal.quote.estimate.project.state:
        context['general_info']['guaranty']['address2'] += ", " + order.proposal.quote.estimate.project.state
    if order.proposal.quote.estimate.project.zip:
        context['general_info']['guaranty']['address2'] += ", " + str(order.proposal.quote.estimate.project)
    if context['general_info']['guaranty']['eng_firm'] == "UNKNOWN":
        context['general_info']['guaranty']['eng_firm'] = "N.S."
    if order.proposal.quote.estimate.engineer.company.address_line_1:
        context['general_info']['guaranty']['eng_firm_address'] = order.proposal.quote.estimate.engineer.company.address_line_1
    if order.proposal.quote.estimate.engineer.company.address_line_2:
        context['general_info']['guaranty']['eng_firm_address'] += ", " + order.proposal.quote.estimate.engineer.company.address_line_2
    if order.proposal.quote.estimate.engineer.company.city:
        context['general_info']['guaranty']['eng_firm_address2'] = order.proposal.quote.estimate.engineer.company.city
    if order.proposal.quote.estimate.engineer.company.state:
        context['general_info']['guaranty']['eng_firm_address2'] += ", " + order.proposal.quote.estimate.engineer.company.state
    if order.proposal.quote.estimate.engineer.company.zip:
        context['general_info']['guaranty']['eng_firm_address2'] += ", " + order.proposal.quote.estimate.engine
    if not context['general_info']['guaranty']['eng_firm_address']:
        context['general_info']['guaranty']['eng_firm_address'] = "N.S."
    if not context['general_info']['guaranty']['eng_firm_address2']:
        context['general_info']['guaranty']['eng_firm_address2'] = "N.S."

    datasheets = order.data_sheets.all()
    page_counter = 1
    # Air Moving
    air_moving_equipments = datasheets.filter(equipment_type__test_sheet__name__iexact='Air Moving').all()
    if len(air_moving_equipments) > 0:
        for air_moving_equipment in air_moving_equipments:
            context['pages'].append({
                'type': 'AIRMOVING',
                'system': air_moving_equipment.fan_no,
                'data': fetch_air_mov_data(air_moving_equipment),
            })
            toc.append({
                'name': air_moving_equipment.fan_no,
                'page': page_counter,
                'level': 0,
                'underline': True
            })
            toc.append({
                'name': 'AIR MOVING EQUIPMENT TEST SHEET',
                'page': page_counter,
                'level': 1,
                'underline': False
            })
            page_counter += 1

            # Air Terminal
            this_air_moving_terminals = datasheets.filter(parent=air_moving_equipment.id, equipment_type__test_sheet__name__iexact='Air Terminal').all().order_by('_type', 'outlet_no')
            if len(this_air_moving_terminals) > 0:
                toc.append({
                    'name': 'AIR TERMINAL TEST SHEET',
                    'page': page_counter,
                    'level': 1,
                    'underline': False
                })
                for _t in [1, 2, 3, 4]:
                    this_terminals = this_air_moving_terminals.filter(_type=_t)
                    if this_terminals:
                        terminals_data = fetch_terminal_data(this_terminals, _t)
                        context['pages'].append(terminals_data)
                        page_counter += 1

    # VAV
    vav_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='V.A.V').all()
    VAV_IN_ONE_PAGE = 12
    if len(vav_equipments) > 0:
        for i in range(math.ceil(vav_equipments.count() / VAV_IN_ONE_PAGE)):
            data = []
            page_items = vav_equipments[i * VAV_IN_ONE_PAGE: (i + 1) * VAV_IN_ONE_PAGE]
            for eq in page_items:
                data.append(fetch_vav_data(eq))
            if len(page_items) < VAV_IN_ONE_PAGE:
                empty_slots = VAV_IN_ONE_PAGE - len(page_items)
                data.extend([{}] * empty_slots)
            context['pages'].append({
                'type': 'VAV',
                'system': 'VAVs',
                'data': data,
            })
            toc.append({
                'name': 'VAVs',
                'page': page_counter,
                'level': 0,
                'underline': True
            })
            toc.append({
                'name': 'V.A.V. BOX SCHEDULE TEST SHEET',
                'page': page_counter,
                'level': 1,
                'underline': False
            })
            page_counter += 1
            # Air Terminal
            this_vav_terminals = datasheets.filter(parent__in=page_items, equipment_type__test_sheet__name__iexact='Air Terminal').all().order_by('_type', 'outlet_no')
            if len(this_vav_terminals) > 0:
                toc.append({
                    'name': 'AIR TERMINAL TEST SHEET',
                    'page': page_counter,
                    'level': 1,
                    'underline': False
                })
            for this_vav_terminal_set in page_items:
                this_vav_terminals = datasheets.filter(parent=this_vav_terminal_set, equipment_type__test_sheet__name__iexact='Air Terminal').all().order_by('_type', 'outlet_no')
                if len(this_vav_terminals) > 0:
                    # toc.append({
                    #     'name': 'AIR TERMINAL TEST SHEET',
                    #     'page': page_counter,
                    #     'level': 1,
                    #     'underline': False
                    # })
                    for _t in [1, 2, 3, 4]:
                        this_terminals = this_vav_terminals.filter(_type=_t)
                        if this_terminals:
                            terminals_data = fetch_terminal_data(this_terminals, _t)
                            context['pages'].append(terminals_data)
                            page_counter += 1

    # Pump
    pump_equipments = datasheets.filter(equipment_type__test_sheet__name__iexact='Pump').all()
    PUMP_IN_ONE_PAGE = 2
    if len(pump_equipments) > 0:
        for i in range(math.ceil(pump_equipments.count() / PUMP_IN_ONE_PAGE)):
            page_items = pump_equipments[i * PUMP_IN_ONE_PAGE: (i + 1) * PUMP_IN_ONE_PAGE]
            data = fetch_pump_data(page_items)
            context['pages'].append({
                'type': 'PUMP',
                'system': 'Pumps',
                'data': data,
            })
            toc.append({
                'name': page_items[0].code,
                'page': page_counter,
                'level': 0,
                'underline': True
            })
            toc.append({
                'name': 'PUMP TEST SHEET',
                'page': page_counter,
                'level': 1,
                'underline': False
            })
            page_counter += 1

    # Velocity Traverse
    velocity_traverse_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='Velocity Traverse').all()
    if len(velocity_traverse_equipments) > 0:
        for eq in velocity_traverse_equipments:
            data = fetch_velocity_data(eq)
            context['pages'].append({
                'type': 'VELOCITY',
                'system': 'VELOCITY TRAVERSE',
                'data': data
            })
            toc.append({
                'name': eq.code,
                'page': page_counter,
                'level': 0,
                'underline': True
            })
            toc.append({
                'name': 'VELOCITY TRAVERSE TEST SHEET',
                'page': page_counter,
                'level': 1,
                'underline': False
            })
            page_counter += 1

    # Flow Measuring
    flow_measuring_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='Flow Measuring').all()
    # 22 - 1 total row
    FLOW_MEASURING_IN_ONE_PAGE = 21
    if len(flow_measuring_equipments) > 0:
        for i in range(math.ceil(flow_measuring_equipments.count() / FLOW_MEASURING_IN_ONE_PAGE)):
            page_items = flow_measuring_equipments[i * FLOW_MEASURING_IN_ONE_PAGE: (i + 1) * FLOW_MEASURING_IN_ONE_PAGE]
            data = fetch_flow_measuring_data(page_items)
            total_design_gpm = data['total_design_gpm']
            total_final_gpm = data['total_final_gpm']
            total_title = data['total_title']
            data = data['data']
            if len(page_items) < FLOW_MEASURING_IN_ONE_PAGE:
                empty_slots = FLOW_MEASURING_IN_ONE_PAGE - len(page_items)
                data.extend([{}] * empty_slots)
            context['pages'].append({
                'type': 'FLOWMEASURING',
                'system': 'Flow Measuring',
                'data': data,
                'total_design_gpm': total_design_gpm,
                'total_final_gpm': total_final_gpm,
                'total_title': total_title,
            })
            toc.append({
                'name': page_items[0].code,
                'page': page_counter,
                'level': 0,
                'underline': True
            })
            toc.append({
                'name': 'FLOW MEASURING TEST SHEET',
                'page': page_counter,
                'level': 1,
                'underline': False
            })
            page_counter += 1

    # Other Terminal
    other_terminal_equipments = datasheets.filter(equipment_type__name__icontains='Other Air Terminal').all()
    for ot in other_terminal_equipments:
        this_terminals_set = datasheets.filter(parent=ot.id, equipment_type__test_sheet__name__iexact='Air Terminal').all().order_by('_type', 'outlet_no')
        if len(this_terminals_set) > 0:
            toc.append({
                'name': ot.fan_no,
                'page': page_counter,
                'level': 0,
                'underline': True
            })
            toc.append({
                'name': 'AIR TERMINAL TEST SHEET',
                'page': page_counter,
                'level': 1,
                'underline': False
            })
            page_counter += 1
            for _t in [1, 2, 3, 4]:
                this_terminals = other_terminal_equipments.filter(_type=_t)
                if this_terminals:
                    terminals_data = fetch_terminal_data(this_terminals, _t)
                    context['pages'].append(terminals_data)

    # Attachment
    attachments = []
    for ds in datasheets:
        if ds.attach:
            url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(ds.attach.file)
            url = url.replace("/media///app/", "")
            image_bytes_list = pdf_to_image_bytes(url)
            image_data_list = [b64encode(img_bytes).decode('utf-8') for img_bytes in image_bytes_list]
            attachments.extend(image_data_list)
            context['pages'].append({
                'type': 'ATTACHMENT',
                'images': attachments,
            })
            toc.append({
                'name': ds.attach_type,
                'page': page_counter,
                'level': 0,
                'underline': False
            })
            page_counter += len(image_data_list)

    # Colored Drawing
    if order.report_colored_drawing:
        url = "http://itab-test-server.airdec.net:8000" + str(order.report_colored_drawing.file)
        url = url.replace("/app/", "/")
        image_bytes_list = pdf_to_image_bytes(url)
        image_data_list = [b64encode(img_bytes).decode('utf-8') for img_bytes in image_bytes_list]
        context['pages'].append({
            'type': 'ATTACHMENT',
            'images': image_data_list,
        })
        toc.append({
            'name': 'AS BUILT MECHANICAL PLAN',
            'page': page_counter,
            'level': 0,
            'underline': False
        })
        page_counter += len(image_data_list)
    context['toc'] = toc

    context['attach_types'] = {
        'SITE PHOTO',
        'THIRD PARTY TEST SHEET',
        'SPECIFIC DRAWING',
        'CHART',
        'CERTIFICATE & CALIBRATION',
        'SUBMITTAL DATA',

        'AS BUILT MECHANICAL PLAN'
    }

    return render(request, "pdf/base_report.html", context)

    if report_sheet.report_type == 1:


        pages = []
        request.session['toc_counter'] = 0
        request.session['continues'] = 0
        table_of_content = []

        def toc_line_maker(title, number_of_pages, level, show_page_number=True, underline=False):
            if show_page_number:
                request.session['toc_counter'] = request.session.get('toc_counter') + 1
                table_of_content.append({
                    'name': title,
                    # 'pages': str(request.session['toc_counter']) + ('-' + str(request.session['toc_counter']+number_of_pages+request.session['continues']-1)) if number_of_pages+request.session['continues'] > 1 else str(request.session['toc_counter']),
                    'pages': str(request.session['toc_counter']),
                    'level': level,
                    'underline': underline
                })
                request.session['toc_counter'] = request.session.get('toc_counter') + number_of_pages - 1
            else:
                table_of_content.append({
                    'name': title,
                    'pages': '',
                    'level': level,
                    'underline': underline
                })
            request.session['continues'] = 0

        def add_rogue_terminal_pages():
            terminal_pages = []
            equipment_in_page = 21
            is_report_pdf = True
            air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                          air_equipment__isnull=True,
                                                                          vav_equipment__isnull=True,
                                                                          type=4).order_by('type', 'other_group', 'outlet_no')


            last_air_equipment_group = 0
            value_list = air_terminal_equipments.values_list('other_group', flat=True).distinct()

            for value in value_list:
                if last_air_equipment_group != value:
                    last_air_equipment_group = value
                    all_air_equipment_terminals = air_terminal_equipments.filter(other_group=value)

                    if len(all_air_equipment_terminals) > 0:
                        terminal_pdf_pages = prepare_terminal_pages(all_air_equipment_terminals, 'OTHER', 0,
                                                                             is_report_pdf,
                                                                             equipment_in_page)
                        toc_line_maker(all_air_equipment_terminals[0].equipment_name, 0, 0, False, True)
                        toc_line_maker('AIR TERMINAL TEST SHEET', len(terminal_pdf_pages), 1, True, False)
                        terminal_pages = terminal_pages + terminal_pdf_pages

            return terminal_pages

        def add_terminal_pages_for_air_moving(air_moving_equipment):
            terminal_pages = []
            equipment_in_page = 21

            air_terminal_equipments = DataSheet.objects.filter(project=report_sheet.project, parent=air_moving_equipment.id).order_by('_type', 'outlet_no')
            if len(air_terminal_equipments) > 0:

                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=1), 1
                )
                terminal_pages.append(air_terminal_pages)

                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=2), 2
                )
                terminal_pages.append(air_terminal_pages)
                
                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=3), 3
                )
                terminal_pages.append(air_terminal_pages)

                air_terminal_pages = fetch_terminal_data(
                    air_terminal_equipments.filter(_type=4), 4
                )
                terminal_pages.append(air_terminal_pages)
            
            terminal_pages = [page for page in terminal_pages if page]
            if terminal_pages:
                terminal_pages = terminal_pages[0]

            return terminal_pages

        def add_vav_pages_using_air_moving(air_moving_equipments):
            vav_pages = []
            is_report_pdf = True
            for air_moving_equipment in air_moving_equipments:
                vav_equipments = DataSheetEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                   inherited_from_air_moving=air_moving_equipment,
                                                                   main_data_entry_completed=True,
                                                                   design_data_entry_completed=True,
                                                                   actual_data_entry_completed=True)

                if len(vav_equipments) > 0:
                    my_sheet = DataSheet.objects.get(test_sheet_type__name__iexact='vav', project=report_sheet.project)

                    equipment_groups = list(map(lambda x: chr(x), range(65, 65 + my_sheet.number_of_equipment_groups)))
                    equipment_in_page = 21
                    last_loop = 0
                    for group in equipment_groups:
                        group_equipments = vav_equipments.filter(equipment_group=group)
                        len_equipments = group_equipments.count()
                        for i in range(math.ceil(len_equipments / equipment_in_page)):
                            last_loop += 1
                            empty_rows = 0
                            page = {
                                'type': 'VAV',
                                'system': 'VAVS ' + air_moving_equipment.secd_set.get(
                                    key__column_title__icontains='fan no.').value,
                                'rows': [],
                                'notes': [],
                                'vavp_available': 0,
                            }
                            for j in range(equipment_in_page):
                                index = i * equipment_in_page + j
                                if index < len_equipments:
                                    page['rows'].append(fetch_vav_equipment_data(group_equipments[index], is_report_pdf))
                                    if group_equipments[index].equipment_type.test_sheet.inheritance:
                                        page['vavp_available'] = 1
                                else:
                                    empty_rows += 1
                            page['empty_rows'] = range(empty_rows)
                            if page['rows']:
                                vav_pages.append(page)

                        if len_equipments > 0:
                            toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', math.ceil(len_equipments / equipment_in_page), 1, True, False)

                        air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                                      vav_equipment__terminal_design_data_entry_completed=True,
                                                                                      vav_equipment__terminal_actual_data_entry_completed=True,
                                                                                      vav_equipment__in=group_equipments.all()) \
                            .order_by('air_equipment__field_order', 'vav_equipment_id', 'type', 'outlet_no')

                        last_vav_equipment_id = 0
                        value_list = air_terminal_equipments.values_list('vav_equipment_id', flat=True).distinct()
                        for value in value_list:
                            if last_vav_equipment_id != value:
                                last_vav_equipment_id = value
                                all_vav_equipment_terminals = air_terminal_equipments.filter(vav_equipment_id=value)

                                if len(all_vav_equipment_terminals) > 0:
                                    vav_terminal_pages = prepare_terminal_pages(all_vav_equipment_terminals, 'SUPPLY', 2,
                                                           is_report_pdf,
                                                           equipment_in_page)
                                    toc_line_maker('AIR TERMINAL TEST SHEET', len(vav_terminal_pages), 2, True, False)
                                    vav_pages = vav_pages + vav_terminal_pages

            return vav_pages

        def add_independent_vav_pages(vav_equipments):
            vav_pages = []

            equipment_in_page = 10  # Number of equipments per page
            total_equipments = vav_equipments.count()

            vav_eqs = []
            for eq in vav_equipments:
                vav_eqs.append(fetch_vav_data(eq))

            # Create VAV pages with 8 equipments each
            for i in range(math.ceil(total_equipments / equipment_in_page)):
                rows = vav_eqs[i * equipment_in_page: (i + 1) * equipment_in_page]
                
                # Only proceed if there are actual rows
                if rows:
                    empty_rows = [None] * (equipment_in_page - len(rows))
                    
                    page = {
                        'type': 'VAV',
                        'system': 'VAVs',
                        'rows': rows + empty_rows,  # Filling the remaining rows with `None` to indicate emptiness
                        'notes': [],
                        'vavp_available': 0,
                        'empty_rows': empty_rows
                    }

                    # Check if any equipment on the page has inheritance, set `vavp_available` if true
                    for equipment_data in rows:  # Only check actual rows, not the empty placeholders
                        if equipment_data.get('inheritance', False):  # Assuming 'inheritance' key in equipment data
                            page['vavp_available'] = 1
                            break

                    vav_pages.append(page)

            # Add TOC line for the VAV schedule only if there are any pages
            if vav_pages:
                toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', len(vav_pages), 1, True, False)

            # Now handle air terminal equipment pages
            air_terminal_equipments = DataSheet.objects.filter(
                project=report_sheet.project,
                parent__in=vav_equipments,
            ).order_by('id', '_type', 'outlet_no')

            if len(air_terminal_equipments) > 0:
                air_terminal_pages = fetch_terminal_data(air_terminal_equipments, 1)
                vav_pages.extend(air_terminal_pages)
                toc_line_maker('AIR TERMINAL TEST SHEET', len(air_terminal_pages), 2, True, False)

            return vav_pages

        def add_velocity_traverse_pages(velocity_traverse_equipments):
            pages = []
            for eq in velocity_traverse_equipments:
                rows = fetch_velocity_data(eq)
                page = {
                    'type': 'VELOCITY',
                    'system': 'VELOCITY TRAVERSE',
                    'rows': rows,
                }
                toc_line_maker('VELOCITY TRAVERSE TEST SHEET', 1, 1, True, False)
                pages.append(page)
            return pages

        while len(air_moving_equipments):
            current_air_moving_equipments = air_moving_equipments[0]
            air_moving_equipments = air_moving_equipments[1:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_air_moving_equipments.fan_no,
                'rows': [
                    fetch_air_mov_data(current_air_moving_equipments),
                ]
            })
            toc_line_maker(current_air_moving_equipments.fan_no, 0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            terminals = add_terminal_pages_for_air_moving(current_air_moving_equipments)
            if terminals:
                toc_line_maker('AIR TERMINAL TEST SHEET', len(terminals), 2, True, False)
                pages.extend(terminals)
            # pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0]])

        if len(indipendent_vav_equipments) > 0:
            toc_line_maker('VAV\'S', 0, 0, False, True)
            pages = pages + add_independent_vav_pages(indipendent_vav_equipments)

        if len(velocity_traverse_equipments) > 0:
            toc_line_maker('VELOCITY TRAVERSE', 0, 0, False, True)
            pages = pages + add_velocity_traverse_pages(velocity_traverse_equipments)

        # pages = pages + add_rogue_terminal_pages()

        # attachment
        for ds in datasheets:
            if ds.attach:
                title = ds.name
                if ds.equipment_type.test_sheet.name == 'Air Moving':
                    title = ds.fan_no
                elif 'V.A.V' in ds.equipment_type.test_sheet.name:
                    title = ds.code

                url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(ds.attach.file)
                url = url.replace("/media///app/", "")
                response = url_request.urlretrieve(url)
                attach = open(response[0], "rb")
                tmp_reader = PdfReader(attach)
                toc_line_maker(f"{ds.attach_type} ({title})", len(tmp_reader.pages), 1, True, False)

        if report_sheet.project.colored_drawing or report_sheet.project.report_colored_drawing:
            toc_line_maker('AS BUILT MECHANICAL PLAN', 1, 1, True, False)

        parameters = {
            'report_sheet': report_sheet,
            'form': {
                'my_sheet': report_sheet,
                'pages': pages,
            },
            'file_name': ('FINAL REPORT {}-{}{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                        report_sheet.project.project_number,'')).upper(),
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
        pdf_name, pdf_path = Render.render_to_file('pdfTemplates/fullTemplate_2.html', parameters, 'FinalReport')
        full_pdf = open(pdf_path, "rb")

        # Append table of content
        parameters = {
            'table_of_content': table_of_content,
            'report_sheet': report_sheet,
            'file_name': ('TABLE OF CONTENT {}-{}{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                            report_sheet.project.project_number, '')).upper(),
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
        pdf_name, pdf_path = Render.render_to_file('pdfTemplates/tocTemplate_2.html', parameters, 'TocReport')
        toc_pdf = open(pdf_path, "rb")
        merger.append(fileobj=toc_pdf)

        parameters = {
            'file_name': ('INSTRUMENT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                     report_sheet.project.project_number)).upper(),
            'report_sheet': report_sheet,
            'report_stamp': report_stamp,
            'datetime': datetime.datetime.now(),
            'license_owner': license_owner,
            'instruction_image': instruction_image,
            'abbreviation_image': abbreviation_image,
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
            'MEDIA_URL': settings.MEDIA_URL,
            'STATIC_URL': settings.STATIC_URL,
            'os': system()
        }

        instrument_pdf = ReportSheet.create_report_pdf(parameters)
        parameters['instrument_pdf'] = instrument_pdf[1]
        instrument = open(instrument_pdf[1], "rb")
        merger.append(fileobj=instrument)
        merger.append(fileobj=full_pdf)

        # append attaches
        for ds in datasheets:
            if ds.attach:
                url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(ds.attach.file)
                url = url.replace("/media///app/", "")
                response = url_request.urlretrieve(url)
                attach = open(response[0], "rb")
                merger.append(fileobj=attach)

        if report_sheet.project.report_colored_drawing:
            # response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.project.report_colored_drawing.file)))
            
            url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(report_sheet.project.report_colored_drawing.file)
            url = url.replace("/media///app/", "")
            print("===" * 15)
            print(url)
            response = url_request.urlretrieve(url)
            drawings = open(response[0], "rb")
            merger.append(fileobj=drawings)
        else:
            # response = url_request.urlretrieve(s3.get_bucket_object('media/' + str(report_sheet.project.colored_drawing.file)))
            url = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + str(report_sheet.project.colored_drawing.file)
            url = url.replace("/media///app/", "")
            print("===" * 15)
            print(url)
            response = url_request.urlretrieve()
            drawings = open(response[0], "rb")
            merger.append(fileobj=drawings)

    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report")):
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report"))
    file_name = ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper() + '.pdf'
    file_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report", file_name)
    s3_path = os.path.join("media/pdfs/report", file_name)
    output = open(file_path, "wb")
    merger.write(output)
    output.close()
    cover.close()
    if not report_sheet.report_type == 1:
        table_of_content_file.close()
        test_sheets.close()
        drawings.close()
    s3.upload_file_to_bucket(file_name=file_path, key=s3_path)

    # return JsonResponse({'reload': True}, safe=False)
    # return JsonResponse({'url': settings.MEDIA_URL + 'pdfs/report/' + ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper()}, safe=False)
    # s3.get_bucket_object(os.path.join("media/pdfs/report", final_pdf_name))
    return s3.get_bucket_object(s3_path)

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
from PyPDF2 import PdfMerger
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






# Template view
def report_cover_template(request):
    return render(request, 'pdfTemplates/coverTemplate.html')


def report_full_template(request):
    return render(request, 'pdfTemplates/fullTemplate_2.html')


def report_report_template(request):
    return render(request, 'pdfTemplates/reportTemplate.html')


def report_toc_template(request):
    return render(request, 'pdfTemplates/tocTemplate_2.html')





def fetch_sheet_equipment_data_2(equipment):

    equipment_data = {
        'fan_no': equipment.fan_no,
        'location': equipment.location,
        'area_served': equipment.area_served,
        'serial_no': equipment.serial_number,
        'manufacturer': equipment.manufacturer,
        'model_no': equipment.model_number,
        'serial_no': equipment.serial_number,
    }

    # se_common_data_set = equipment
    e_custom_field_set = equipment.form_fields["design"]
    se_actual_data_set = equipment.form_fields["actual"]
    if 'Total C.F.M. Fan' in e_custom_field_set:
        equipment_data['total_cfm_fan'] = {
            'design': e_custom_field_set['Total C.F.M. Fan']['value'],
            'actual': se_actual_data_set['Total C.F.M. Fan']['value']
        }
    else:
        equipment_data['total_cfm_fan'] = {
            'design': '',
            'actual': ''
        }
    if 'Air Temp. In Cooling' in e_custom_field_set:
        equipment_data['air_temp_in_cooling'] = {
            'design': e_custom_field_set['Air Temp. In Cooling']['value'],
            'actual': se_actual_data_set['Air Temp. In Cooling']['value']
        }
    else:
        equipment_data['air_temp_in_cooling'] = {
            'design': '',
            'actual': ''
        }
    if 'Total C.F.M. Outlets' in e_custom_field_set:
        equipment_data['total_cfm_outlets'] = {
            'design': e_custom_field_set['Total C.F.M. Outlets']['value'],
            'actual': se_actual_data_set['Total C.F.M. Outlets']['value']
        }
    else:
        equipment_data['total_cfm_outlets'] = {
            'design': '',
            'actual': ''
        }
    if 'Air Temp. Out Cooling' in e_custom_field_set:
        equipment_data['air_temp_out_cooling'] = {
            'design': e_custom_field_set['Air Temp. Out Cooling']['value'],
            'actual': se_actual_data_set['Air Temp. Out Cooling']['value']
        }
    else:
        equipment_data['air_temp_out_cooling'] = {
            'design': '',
            'actual': ''
        }
    if 'Return Air C.F.M.' in e_custom_field_set:
        equipment_data['return_air_cfm'] = {
            'design': e_custom_field_set['Return Air C.F.M.']['value'],
            'actual': se_actual_data_set['Return Air C.F.M.']['value']
        }
    else:
        equipment_data['return_air_cfm'] = {
            'design': '',
            'actual': ''
        }
    if 'RH %' in e_custom_field_set:
        equipment_data['rh'] = {
            'design': e_custom_field_set['RH %']['value'],
            'actual': se_actual_data_set['RH %']['value']
        }
    else:
        equipment_data['rh'] = {
            'design': '',
            'actual': ''
        }
    if 'Outdoor Air C.F.M.' in e_custom_field_set:
        equipment_data['outdoor_air_cfm'] = {
            'design': e_custom_field_set['Outdoor Air C.F.M.']['value'],
            'actual': se_actual_data_set['Outdoor Air C.F.M.']['value']
        }
    else:
        equipment_data['outdoor_air_cfm'] = {
            'design': '',
            'actual': ''
        }
    if 'Air Temp. In Heating' in e_custom_field_set:
        equipment_data['air_temp_in_heating'] = {
            'design': e_custom_field_set['Air Temp. In Heating']['value'],
            'actual': se_actual_data_set['Air Temp. In Heating']['value']
        }
    else:
        equipment_data['air_temp_in_heating'] = {
            'design': '',
            'actual': ''
        }
    if 'Total SP (Ext. SP)' in e_custom_field_set:
        equipment_data['total_sp_ext_sp'] = {
            'design': e_custom_field_set['Total SP (Ext. SP)']['value'],
            'actual': se_actual_data_set['Total SP (Ext. SP)']['value']
        }
    else:
        equipment_data['total_sp_ext_sp'] = {
            'design': '',
            'actual': ''
        }
    if 'Air Temp. Out Heating' in e_custom_field_set:
        equipment_data['air_temp_out_heating'] = {
            'design': e_custom_field_set['Air Temp. Out Heating']['value'],
            'actual': se_actual_data_set['Air Temp. Out Heating']['value']
        }
    else:
        equipment_data['air_temp_out_heating'] = {
            'design': '',
            'actual': ''
        }
    if 'Fan (Unit) Suction Pressure' in e_custom_field_set:
        equipment_data['fan_unit_suction_pressure'] = {
            'design': e_custom_field_set['Fan (Unit) Suction Pressure']['value'],
            'actual': se_actual_data_set['Fan (Unit) Suction Pressure']['value']
        }
    else:
        equipment_data['fan_unit_suction_pressure'] = {
            'design': '',
            'actual': ''
        }
    if 'Ambient Temp.' in e_custom_field_set:
        equipment_data['ambient_temp'] = {
            'design': e_custom_field_set['Ambient Temp.']['value'],
            'actual': se_actual_data_set['Ambient Temp.']['value']
        }
    else:
        equipment_data['ambient_temp'] = {
            'design': '',
            'actual': ''
        }
    if 'Discharge Pressure, Fan / Unit' in e_custom_field_set:
        equipment_data['discharge_pressure_fan_unit'] = {
            'design': e_custom_field_set['Discharge Pressure, Fan / Unit']['value'],
            'actual': se_actual_data_set['Discharge Pressure, Fan / Unit']['value']
        }
    else:
        equipment_data['discharge_pressure_fan_unit'] = {
            'design': '',
            'actual': ''
        }
    if 'O.A. Damper Poss.' in e_custom_field_set:
        equipment_data['oa_damper_poss'] = {
            'design': e_custom_field_set['O.A. Damper Poss.']['value'],
            'actual': se_actual_data_set['O.A. Damper Poss.']['value']
        }
    else:
        equipment_data['oa_damper_poss'] = {
            'design': '',
            'actual': ''
        }
    if 'Fan R.P.M.' in e_custom_field_set:
        equipment_data['fan_rpm'] = {
            'design': e_custom_field_set['Fan R.P.M.']['value'],
            'actual': se_actual_data_set['Fan R.P.M.']['value']
        }
    else:
        equipment_data['fan_rpm'] = {
            'design': '',
            'actual': ''
        }
    if 'GPM' in e_custom_field_set:
        equipment_data['gpm'] = {
            'design': e_custom_field_set['GPM']['value'],
            'actual': se_actual_data_set['GPM']['value']
        }
    else:
        equipment_data['gpm'] = {
            'design': '',
            'actual': ''
        }
    if 'H.P.' in e_custom_field_set:
        equipment_data['hp'] = {
            'design': e_custom_field_set['H.P.']['value'],
            'actual': se_actual_data_set['H.P.']['value']
        }
    else:
        equipment_data['hp'] = {
            'design': '',
            'actual': ''
        }
    if 'Belt Size' in e_custom_field_set:
        equipment_data['belt_size'] = {
            'actual': se_actual_data_set['Belt Size']['value']
        }
    else:
        equipment_data['belt_size'] = {
            'actual': ''
        }
    if 'Motor Pully' in e_custom_field_set:
        equipment_data['motor_pully'] = {
            'actual': se_actual_data_set['Motor Pully']['value']
        }
    else:
        equipment_data['motor_pully'] = {
            'actual': ''
        }
    if 'Voltage' in e_custom_field_set:
        equipment_data['voltage'] = {
            'design': e_custom_field_set['Voltage']['value'],
            'actual': se_actual_data_set['Voltage']['value']
        }
    else:
        equipment_data['voltage'] = {
            'design': '',
            'actual': ''
        }
    if 'Fan Pully' in e_custom_field_set:
        equipment_data['fan_pully'] = {
            'actual': se_actual_data_set['Fan Pully']['value']
        }
    else:
        equipment_data['fan_pully'] = {
            'actual': ''
        }
    if 'Phase' in e_custom_field_set:
        equipment_data['phase'] = {
            'design': e_custom_field_set['Phase']['value'],
            'actual': se_actual_data_set['Phase']['value']
        }
    else:
        equipment_data['phase'] = {
            'design': '',
            'actual': ''
        }
    if 'C to C' in e_custom_field_set:
        equipment_data['c_to_c'] = {
            'actual': se_actual_data_set['C to C']['value']
        }
    else:
        equipment_data['c_to_c'] = {
            'actual': ''
        }
    if 'Amperage' in e_custom_field_set:
        equipment_data['amperage'] = {
            'design': e_custom_field_set['Amperage']['value'],
            'actual': se_actual_data_set['Amperage']['value']
        }
    else:
        equipment_data['amperage'] = {
            'design': '',
            'actual': ''
        }
    if 'Motor Shaft' in e_custom_field_set:
        equipment_data['motor_shaft'] = {
            'actual': se_actual_data_set['Motor Shaft']['value']
        }
    else:
        equipment_data['motor_shaft'] = {
            'actual': ''
        }
    if 'B.H.P. (Calc.)' in e_custom_field_set:
        equipment_data['bhp'] = {
            'design': e_custom_field_set['B.H.P. (Calc.)']['value'],
            'actual': se_actual_data_set['B.H.P. (Calc.)']['value']
        }
    else:
        equipment_data['bhp'] = {
            'design': '',
            'actual': ''
        }
    if 'Fan Shaft' in e_custom_field_set:
        equipment_data['fan_shaft'] = {
            'actual': se_actual_data_set['Fan Shaft']['value']
        }
    else:
        equipment_data['fan_shaft'] = {
            'actual': ''
        }
    if 'Frame' in e_custom_field_set:
        equipment_data['frame'] = {
            'design': e_custom_field_set['Frame']['value'],
            'actual': se_actual_data_set['Frame']['value']
        }
    else:
        equipment_data['frame'] = {
            'design': '',
            'actual': ''
        }
    if 'VFD / HZ' in e_custom_field_set:
        equipment_data['vfd_hz'] = {
            'actual': se_actual_data_set['VFD / HZ']['value']
        }
    else:
        equipment_data['vfd_hz'] = {
            'actual': ''
        }
    if 'S.F. / Code' in e_custom_field_set:
        equipment_data['sf_code'] = {
            'design': e_custom_field_set['S.F. / Code']['value'],
            'actual': se_actual_data_set['S.F. / Code']['value']
        }
    else:
        equipment_data['sf_code'] = {
            'design': '',
            'actual': ''
        }
    if 'Filter Size' in e_custom_field_set:
        equipment_data['filter_size'] = {
            'actual': se_actual_data_set['Filter Size']['value']
        }
    else:
        equipment_data['filter_size'] = {
            'actual': ''
        }
    if 'Motor RPM' in e_custom_field_set:
        equipment_data['motor_rpm'] = {
            'design': e_custom_field_set['Motor RPM']['value'],
            'actual': se_actual_data_set['Motor RPM']['value']
        }
    else:
        equipment_data['motor_rpm'] = {
            'design': '',
            'actual': ''
        }
    if 'Filter Model' in e_custom_field_set:
        equipment_data['filter_model'] = {
            'actual': se_actual_data_set['Filter Model']['value']
        }
    else:
        equipment_data['filter_model'] = {
            'actual': ''
        }
    
    equipment_data['note'] = ""
    if 'Note' in e_custom_field_set:
        equipment_data['note'] += " " + e_custom_field_set['Note']['value'] if e_custom_field_set['Note']['value'] else ""
    if 'Note' in se_actual_data_set:
        equipment_data['note'] += " " + se_actual_data_set['Note']['value'] if se_actual_data_set['Note']['value'] else ""

    for key, val in equipment_data.items():
        if (val is None) or (val == 'None') or (not val):
            equipment_data[key] = ''

    return equipment_data


def fetch_vavsheet_equipment_data_2(this_sheet_equipment, is_report_pdf: bool):
    inherit = False
    if this_sheet_equipment.equipment_type.test_sheet.inheritance:
        inherit = True
    design_field_set = this_sheet_equipment.form_fields["design"]
    actual_field_set = this_sheet_equipment.form_fields["actual"]
    equipment_data = {
        'inherit': inherit,
        'address': design_field_set["Address"]["value"] if "Address" in design_field_set else "",
        'code': design_field_set["Code"]["value"] if "Code" in design_field_set else "",
        'type': design_field_set["Type"]["value"] if "Type" in design_field_set else "",
        'size_kw': design_field_set["Size / KW"]["value"] if "Size / KW" in design_field_set else "",
        'fan': design_field_set["Fan %"]["value"] if "Fan %" in design_field_set else "",
        'fan_cfm': design_field_set["Fan CFM"]["value"] if "Fan CFM" in design_field_set else "",
        'min_cfm': {
            'design': design_field_set["Min. CFM"]["value"] if "Min. CFM" in design_field_set else "",
            'actual': actual_field_set["Min. CFM"]["value"] if "Min. CFM" in actual_field_set else ""
        },
        'max_cfm': {
            'design': design_field_set["Max. CFM"]["value"] if "Max. CFM" in design_field_set else "",
            'actual': actual_field_set["Max. CFM"]["value"] if "Max. CFM" in actual_field_set else ""
        },
        'kf': actual_field_set["K.F."]["value"] if "K.F." in actual_field_set else "",
        'min_fan_cfm': actual_field_set["Min. / Fan CFM"]["value"] if "Min. / Fan CFM" in actual_field_set else "",
        'model_number': this_sheet_equipment.model_number,
        'HP': "",
        'make': "",
        'fan_volt': actual_field_set["Fan volt"]["value"] if "Fan volt" in actual_field_set else "",
        'fan_amp': actual_field_set["Fan Amp"]["value"] if "Fan Amp" in actual_field_set else "",
        't_in': actual_field_set["T In"]["value"] if "T In" in actual_field_set else "",
        'fan_va': actual_field_set["Fan V / A"]["value"] if "Fan V / A" in actual_field_set else "",
        'heat_va': {
            'design': design_field_set["Heat V / A"]["value"] if "Heat V / A" in design_field_set else "",
            'actual': actual_field_set["Heat V / A"]["value"] if "Heat V / A" in actual_field_set else ""
        },
        't_out': actual_field_set["T Out"]["value"] if "T Out" in actual_field_set else "",
    }

    equipment_data['note'] = ""
    if 'Note' in design_field_set:
        equipment_data['note'] += " " + design_field_set['Note']['value'] if design_field_set['Note']['value'] else ""
    if 'Note' in actual_field_set:
        equipment_data['note'] += " " + actual_field_set['Note']['value'] if actual_field_set['Note']['value'] else ""

    for key, val in equipment_data.items():
        if (val is None) or (val == 'None') or (not val):
            equipment_data[key] = ''

    return equipment_data


def prepare_terminal_pages_new(equipment_list, page_type, airOrVav, is_report_pdf, equipment_in_page):
    pages = []
    design_total = 0
    initial_total = 0
    final_total = 0
    for equipment in equipment_list.all():
        cfm = equipment.form_fields['design']['CFM']["value"] if "CFM" in equipment.form_fields['design'] else None
        if cfm:
            design_total += int(cfm)
        else:
            if airOrVav == 1:
                design_total = equipment.fan_no
        if is_report_pdf:
            initial_cfm = equipment.form_fields['actual']['Initial CFM']["value"] if "Initial CFM" in equipment.form_fields['actual'] else None
            if initial_cfm and initial_cfm != '':
                initial_total += int(initial_cfm)
            final_cfm = equipment.form_fields['actual']['Final CFM']["value"] if "Final CFM" in equipment.form_fields['actual'] else None
            if final_cfm and final_cfm != '':
                final_total += int(final_cfm)
    if len(equipment_list) > (equipment_in_page - 1):
        equipments_data = []
        for equipment in equipment_list[0:equipment_in_page - 1]:
            equipments_data.append(fetch_sheet_equipment_data_2(equipment))
        pages.append({
            'type': page_type,
            'eq_name': equipment_list[0].name if airOrVav == 0 else '',
            'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].fan_no if airOrVav == 1 else equipment_list[0].code,
            'rows': [
                'title',
                equipments_data
            ]
        })
        remaining_rows = equipment_list[equipment_in_page:]
        while len(remaining_rows) > equipment_in_page:
            equipments_data = []
            for equipment in remaining_rows[0:equipment_in_page]:
                equipments_data.append(fetch_sheet_equipment_data_2(equipment))
            pages.append({
                'type': page_type,
            'eq_name': equipment_list[0].name if airOrVav == 0 else '',
                'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].fan_no if airOrVav == 1 else equipment_list[0].code,
                'rows': [
                    equipments_data
                ]
            })
            remaining_rows = remaining_rows[equipment_in_page + 1:]
        equipments_data = []
        for equipment in remaining_rows:
            equipments_data.append(fetch_sheet_equipment_data_2(equipment))
        pages.append({
            'type': page_type,
            'eq_name': equipment_list[0].name if airOrVav == 0 else '',
            'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].fan_no if airOrVav == 1 else equipment_list[0].code,
            'rows': [
                equipments_data,
                {
                    'd_cfm_total': design_total,
                    'i_cfm_total': initial_total,
                    'f_cfm_total': final_total,
                    'empty_rows': range(equipment_in_page - len(remaining_rows) - 1),
                }
            ]
        })
    else:
        equipments_data = []
        for equipment in equipment_list:
            equipments_data.append(fetch_sheet_equipment_data_2(equipment))

        pages.append({
            'type': page_type,
            'eq_name': equipment_list[0].name if airOrVav == 0 else '',
            'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].fan_no if airOrVav == 1 else equipment_list[0].code,
            'rows': [
                'title',
                equipments_data,
                {
                    'd_cfm_total': design_total,
                    'i_cfm_total': initial_total,
                    'f_cfm_total': final_total,
                    'empty_rows': range(equipment_in_page - len(equipment_list) - 2),
                }
            ]
        })
    return pages


def prepare_terminal_pages_new(terminals):
    pages = []
    equipment_in_page = 21
    terminals_by_type = {
        'SUPPLY': [],
        'RETURN': [],
        'EXHAUST': [],
        'OTHER': []
    }

    for terminal in terminals:
        _type = None
        if terminal._type == 0:
            _type = 'SUPPLY'
        elif terminal._type == 1:
            _type = 'RETURN'
        elif terminal._type == 2:
            _type = 'EXHAUST'
        elif terminal._type == 3:
            _type = 'OTHER'
        design_field_set = terminal.form_fields["design"]
        actual_field_set = terminal.form_fields["actual"]
        equipment_data = {
            'room_no': design_field_set["Room No."]["value"] if "Room No." in design_field_set else "",
            'outlet_no': design_field_set["Outlet No."]["value"] if "Outlet No." in design_field_set else "",
            'code': design_field_set["Code"]["value"] if "Code" in design_field_set else "",
            'size': design_field_set["Size"]["value"] if "Size" in design_field_set else "",
            'ak_factor': design_field_set["AK Factor"]["value"] if "AK Factor" in design_field_set else "",
            'fpm': {
                'design': design_field_set["FPM"]["value"] if "FPM" in design_field_set else "",
                'initial': actual_field_set["Initial FPM"]["value"] if "Initial FPM" in actual_field_set else "",
                'final': actual_field_set["Final FPM"]["value"] if "Final FPM" in actual_field_set else ""
            },
            'cfm': {
                'design': design_field_set["CFM"]["value"] if "CFM" in design_field_set else "",
                'initial': actual_field_set["Initial CFM"]["value"] if "Initial CFM" in actual_field_set else "",
                'final': actual_field_set["Final CFM"]["value"] if "Final CFM" in actual_field_set else ""
            },
            'note': "",
            'title': terminal.fan_no,
            'type': _type,
        }
        terminals_by_type[_type].append(equipment_data)

    # Put each terminal (by type) into pages by equipment_in_page count
    for _type, terminals in terminals_by_type.items():
        if len(terminals) == 0:
            continue  # Skip this type if there are no terminals
        if len(terminals) > (equipment_in_page - 1):
            equipments_data = []
            for terminal in terminals[0:equipment_in_page - 1]:
                equipments_data.append(terminal)
            pages.append({
                'type': 'TERMINAL',
                'eq_name': "Terminal",
                'system': _type,
                'rows': equipments_data
            })
            remaining_rows = terminals[equipment_in_page:]
            while len(remaining_rows) > equipment_in_page:
                equipments_data = []
                for terminal in remaining_rows[0:equipment_in_page]:
                    equipments_data.append(terminal)
                pages.append({
                    'type': 'TERMINAL',
                    'eq_name': "Terminal",
                    'system': _type,
                    'rows': equipments_data
                })
                remaining_rows = remaining_rows[equipment_in_page + 1:]
            equipments_data = []
            for terminal in remaining_rows:
                equipments_data.append(terminal)
            # Extend the list with empty objects until it reaches the length of equipment_in_page
            equipments_data.extend([{}] * (equipment_in_page - len(equipments_data)))
            pages.append({
                'type': 'TERMINAL',
                'eq_name': "Terminal",
                'system': _type,
                'rows': equipments_data
            })
        else:
            equipments_data = []
            for terminal in terminals:
                equipments_data.append(terminal)
            # Extend the list with empty objects until it reaches the length of equipment_in_page
            equipments_data.extend([{}] * (equipment_in_page - len(equipments_data)))
            pages.append({
                'type': 'TERMINAL',
                'eq_name': "Terminal",
                'system': _type,
                'rows': equipments_data
            })

    return pages


@login_required
def report_sheet_recreate_call(request, order_id):
    s3 = S3()
    report_sheet = ReportSheet.objects.get_or_create(project=order_id, report_type=1)[0]
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
        datasheets = DataSheet.objects.filter(project=report_sheet.project)
        air_moving_equipments = datasheets.filter(equipment_type__test_sheet__name__iexact='Air Moving').all()
        indipendent_vav_equipments = datasheets.exclude(
            equipment_type__test_sheet__name__iexact='Air Moving').exclude(
            equipment_type__test_sheet__name__iexact='Air Terminal'
        ).all()

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

        def add_terminal_pages_for_air_moving(air_moving_equipments):
            terminal_pages = []
            number_of_total_pages = 0
            for air_moving_equipment in air_moving_equipments:
                equipment_in_page = 21
                is_report_pdf = True
                air_terminal_equipments = DataSheet.objects.filter(project=report_sheet.project, parent=air_moving_equipment).order_by('_type', 'outlet_no')

                if len(air_terminal_equipments) > 0:
                    this_terminal_pages = prepare_terminal_pages_new(air_terminal_equipments)
                    number_of_total_pages = number_of_total_pages + len(this_terminal_pages)
                    terminal_pages.append(this_terminal_pages)

                # last_air_equipment_id = 0
                # value_list = air_terminal_equipments.values_list('id', flat=True).distinct()
                # for value in value_list:
                #     if last_air_equipment_id != value:
                #         last_air_equipment_id = value
                #         all_air_equipment_terminals = air_terminal_equipments.filter(id=value)
                #         type_list = all_air_equipment_terminals.values_list('_type', flat=True).distinct()
                #         group_by_terminal_type = {}
                #         for terminal_type in type_list:
                #             group_by_terminal_type[terminal_type] = all_air_equipment_terminals.filter(_type=terminal_type)

                #         done_types = []
                #         for terminal_type in type_list:
                #             if terminal_type not in done_types:
                #                 if terminal_type == 1:
                #                     adding_supply_pages = prepare_terminal_pages_new(group_by_terminal_type[1], 'SUPPLY', 1,
                #                                                       is_report_pdf,
                #                                                       equipment_in_page)
                #                     terminal_pages = terminal_pages + adding_supply_pages
                #                     number_of_total_pages = number_of_total_pages + len(adding_supply_pages)
                #                 elif terminal_type == 2:
                #                     adding_return_pages = prepare_terminal_pages_new(group_by_terminal_type[2], 'RETURN', 1,
                #                                                                  is_report_pdf,
                #                                                                  equipment_in_page)
                #                     terminal_pages = terminal_pages + adding_return_pages
                #                     number_of_total_pages = number_of_total_pages + len(adding_return_pages)
                #                 elif terminal_type == 3:
                #                     adding_outside_pages = prepare_terminal_pages_new(group_by_terminal_type[3], 'OUTSIDE', 1,
                #                                                                  is_report_pdf,
                #                                                                  equipment_in_page)
                #                     terminal_pages = terminal_pages + adding_outside_pages
                #                     number_of_total_pages = number_of_total_pages + len(adding_outside_pages)
                #                 done_types.append(terminal_type)


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

            equipment_in_page = 10  # Number of equipments per page
            total_equipments = vav_equipments.count()

            vav_eqs = []
            for eq in vav_equipments:
                vav_eqs.append(fetch_vavsheet_equipment_data_2(eq, is_report_pdf))

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
                air_terminal_pages = prepare_terminal_pages_new(air_terminal_equipments)
                vav_pages.extend(air_terminal_pages)
                toc_line_maker('AIR TERMINAL TEST SHEET', len(air_terminal_pages), 2, True, False)

            # total_air_equipment_pages = 0
            # vav_air_terminal_equipment_list = []
            # value_list = air_terminal_equipments.values_list('id', flat=True).distinct()

            # for value in value_list:
            #     if value not in vav_air_terminal_equipment_list:
            #         all_vav_equipment_terminals = air_terminal_equipments.filter(id=value)

            #         if all_vav_equipment_terminals.exists():
            #             air_terminal_pages = prepare_terminal_pages_new(
            #                 all_vav_equipment_terminals,
            #                 'SUPPLY',
            #                 2,
            #                 is_report_pdf,
            #                 21
            #             )
            #             total_air_equipment_pages += len(air_terminal_pages)
            #             vav_pages.extend(air_terminal_pages)

            #         vav_air_terminal_equipment_list.append(value)

            # # Add TOC line for the air terminal test sheets only if there are any air terminal pages
            # if total_air_equipment_pages > 0:
            #     toc_line_maker('AIR TERMINAL TEST SHEET', total_air_equipment_pages, 2, True, False)

            return vav_pages

        while len(air_moving_equipments):
            current_air_moving_equipments = air_moving_equipments[0]
            air_moving_equipments = air_moving_equipments[1:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_air_moving_equipments.fan_no,
                'rows': [
                    fetch_sheet_equipment_data_2(current_air_moving_equipments),
                ]
            })
            toc_line_maker(current_air_moving_equipments.fan_no, 0, 0, False, True)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1, True, False)
            pages = pages + add_terminal_pages_for_air_moving([current_air_moving_equipments])
            # pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0]])

        if len(indipendent_vav_equipments) > 0:
            toc_line_maker('VAV\'S', 0, 0, False, True)
            pages = pages + add_independent_vav_pages(indipendent_vav_equipments)

        # pages = pages + add_rogue_terminal_pages()

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

    # return JsonResponse({'reload': True}, safe=False)
    # return JsonResponse({'url': settings.MEDIA_URL + 'pdfs/report/' + ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper()}, safe=False)
    # s3.get_bucket_object(os.path.join("media/pdfs/report", final_pdf_name))
    return s3.get_bucket_object(s3_path)



# def get_license_info_values(keys):
#     return {key: LicenseInfo.objects.get(key=key).value for key in keys}

# def get_license_files_values(keys):
#     return {key: LicenseFiles.objects.get(key=key).value for key in keys}

# def get_report_sheet(order_id):
#     return ReportSheet.objects.get_or_create(project=get_object_or_404(Order, id=order_id))[0]

# def get_common_parameters(report_sheet, license_info, license_files):
#     return {
#         'report_sheet': report_sheet,
#         'license_owner': license_info['OwnerName'],
#         'owner_title': license_info['OwnerTitle'],
#         'owner_address_line1': license_info['OwnerAddressLine1'],
#         'owner_address_line2': license_info['OwnerAddressLine2'],
#         'owner_tel': license_info['OwnerTel'],
#         'owner_fax': license_info['OwnerFax'],
#         'owner_web': license_info['OwnerWeb'],
#         'owner_mail': license_info['OwnerMail'],
#         'owner_signature': license_files['OwnerSignature'],
#         'owner_logo': license_files['OwnerLogo'],
#         'pdf_header_logo': license_files['PDFHeaderLogo'],
#         'pdf_header_text': license_info['PDFHeaderText'],
#         'company_name': license_info['CompanyName'],
#         'WEB_URL': settings.WEB_URL,
#         'MEDIA_URL': settings.MEDIA_URL,
#         'STATIC_URL': settings.STATIC_URL,
#         'os': system(),
#         'datetime': datetime.datetime.now(),
#     }

# @contextmanager
# def open_file(file_path, mode='rb'):
#     file = open(file_path, mode)
#     try:
#         yield file
#     finally:
#         file.close()

# def merge_pdf_files(output_path, *file_paths):
#     merger = PdfMerger()
#     for file_path in file_paths:
#         with open_file(file_path) as file:
#             merger.append(fileobj=file)
#     with open_file(output_path, 'wb') as output:
#         merger.write(output)

# def create_cover_pdf(parameters, project_name, project_number):
#     parameters['file_name'] = f'COVER SHEET {project_name}-{project_number}'.upper()
#     cover_pdf = ReportSheet.create_cover_pdf(parameters)
#     parameters['cover_pdf'] = cover_pdf[1]
#     return cover_pdf[1]

# def create_final_report(parameters, report_sheet, project_name, project_number):
#     parameters['file_name'] = f'FINAL REPORT {project_name}-{project_number}'.upper()
#     pdf_name, pdf_path = Render.render_to_file('pdfTemplates/fullTemplate.html', parameters, 'FinalReport')
#     return pdf_path

# def create_toc_pdf(parameters, project_name, project_number):
#     parameters['file_name'] = f'TABLE OF CONTENT {project_name}-{project_number}'.upper()
#     pdf_name, pdf_path = Render.render_to_file('bghs/tocTemplate.html', parameters, 'TocReport')
#     return pdf_path

# def create_instrument_pdf(parameters, project_name, project_number):
#     parameters['file_name'] = f'INSTRUMENT SHEET {project_name}-{project_number}'.upper()
#     instrument_pdf = ReportSheet.create_report_pdf(parameters)
#     parameters['instrument_pdf'] = instrument_pdf[1]
#     return instrument_pdf[1]

# def report_sheet_recreate_call(request, order_id):
#     s3 = S3()
#     report_sheet = get_report_sheet(order_id)
#     project_name = report_sheet.project.proposal.quote.estimate.project.name
#     project_number = report_sheet.project.project_number
    
#     license_info_keys = [
#         'OwnerName', 'OwnerTitle', 'OwnerTel', 'OwnerFax', 'OwnerWeb', 
#         'OwnerMail', 'CompanyName', 'OwnerAddressLine1', 'OwnerAddressLine2', 'PDFHeaderText'
#     ]
#     license_file_keys = [
#         'ReportStamp', 'InstructionReport', 'AbbreviationReport', 
#         'OwnerSignature', 'OwnerLogo', 'PDFHeaderLogo'
#     ]
    
#     license_info = get_license_info_values(license_info_keys)
#     license_files = get_license_files_values(license_file_keys)
    
#     parameters = get_common_parameters(report_sheet, license_info, license_files)

#     cover_pdf_path = create_cover_pdf(parameters, project_name, project_number)
#     final_report_path = create_final_report(parameters, report_sheet, project_name, project_number)
#     toc_pdf_path = create_toc_pdf(parameters, project_name, project_number)
#     instrument_pdf_path = create_instrument_pdf(parameters, project_name, project_number)
    
#     output_dir = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report")
#     os.makedirs(output_dir, exist_ok=True)
#     final_pdf_name = f'FINAL SHEET {project_name}-{project_number}'.upper() + '.pdf'
#     final_pdf_path = os.path.join(output_dir, final_pdf_name)
    
#     merge_pdf_files(final_pdf_path, cover_pdf_path, toc_pdf_path, instrument_pdf_path, final_report_path)
    
#     s3.upload_file_to_bucket(file_name=final_pdf_path, key=os.path.join("media/pdfs/report", final_pdf_name))
#     return s3.get_bucket_object(os.path.join("media/pdfs/report", final_pdf_name))

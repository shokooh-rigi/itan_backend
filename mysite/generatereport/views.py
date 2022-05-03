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
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from django.db.models import Count
from PyPDF2 import PdfFileMerger
import random
from ..settings import MEDIA_URL_NOSLASH
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

    object_list = ReportSheet.objects.all()

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "reportSheetList.html", parameters)


@login_required
def report_sheet_add(request):
    form = ReportSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=ReportSheet.objects.values_list('project_id')).order_by('project_number')
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
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
        'STATIC_URL': STATIC_URL,
        'os': system()
    }

    cover_pdf = ReportSheet.create_cover_pdf(parameters)
    parameters['cover_pdf'] = cover_pdf[1]

    parameters['file_name'] = ('REPORT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                           report_sheet.project.project_number)).upper()
    merger = PdfFileMerger()
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

        def toc_line_maker(title, number_of_pages, level, show_page_number=True):
            if show_page_number:
                request.session['toc_counter'] = request.session.get('toc_counter') + 1
                table_of_content.append({
                    'name': title,
                    'pages': str(request.session['toc_counter']) + ('-' + str(request.session['toc_counter']+number_of_pages+request.session['continues']-1)) if number_of_pages+request.session['continues'] > 1 else str(request.session['toc_counter']),
                    'level': level
                })
                request.session['toc_counter'] = request.session.get('toc_counter') + number_of_pages - 1
            else:
                table_of_content.append({
                    'name': title,
                    'pages': '',
                    'level': level
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
                        'system': 'VELOCITY ' + air_moving_equipment.sheetequipmentcommondata_set.get(
                            key__column_title__icontains='fan no.').value,
                        'rows': [velocity_equipment],
                        'max_row': range(14),
                        'max_col': range(14),
                    })

            toc_line_maker('VELOCITY TRAVERSE TEST SHEET', number_of_total_pages, 1)

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
            toc_line_maker('PUMP TEST SHEET', total_pages, 0)

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
                        toc_line_maker(all_air_equipment_terminals[0].equipment_name, 0, 0, False)
                        toc_line_maker('AIR TERMINAL TEST SHEET', len(terminal_pdf_pages), 1)
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

                        all_supply_terminals = group_by_terminal_type[1]
                        all_return_terminals = group_by_terminal_type[2]
                        all_outside_terminals = group_by_terminal_type[3]

                        adding_supply_pages = prepare_terminal_pages(all_supply_terminals, 'SUPPLY', 1,
                                                                     is_report_pdf,
                                                                     equipment_in_page)

                        adding_return_pages = prepare_terminal_pages(all_return_terminals, 'RETURN', 1,
                                                                     is_report_pdf,
                                                                     equipment_in_page)

                        adding_outside_pages = prepare_terminal_pages(all_outside_terminals, 'OUTSIDE', 1,
                                                                     is_report_pdf,
                                                                     equipment_in_page)

                        number_of_total_pages = number_of_total_pages + len(adding_supply_pages) + len(adding_return_pages) + len(adding_outside_pages)

                        terminal_pages = terminal_pages + adding_supply_pages
                        terminal_pages = terminal_pages + adding_return_pages
                        terminal_pages = terminal_pages + adding_outside_pages

            toc_line_maker('AIR TERMINAL TEST SHEET', number_of_total_pages, 1, True)
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
                            'system': 'VAVS ' + air_moving_equipment.sheetequipmentcommondata_set.get(
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
                        toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', math.ceil(len_equipments / equipment_in_page), 1)

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
                                toc_line_maker('AIR TERMINAL TEST SHEET', len(vav_terminal_pages), 2)
                                vav_pages = vav_pages + vav_terminal_pages

            return vav_pages

        def add_independent_vav_pages(vav_equipments):
            vav_pages = []
            equipment_in_page = 22
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
                    toc_line_maker('V.A.V. BOX SCHEDULE TEST SHEET', math.ceil(len_equipments / equipment_in_page), 1)

                air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet__project=report_sheet.project,
                                                                              vav_equipment__terminal_design_data_entry_completed=True,
                                                                              vav_equipment__terminal_actual_data_entry_completed=True,
                                                                              vav_equipment__in=group_equipments.all()) \
                    .order_by('air_equipment__field_order', 'air_equipment_id', 'type', 'outlet_no')

                if len(air_terminal_equipments) > 0:

                    air_terminal_pages = prepare_terminal_pages(air_terminal_equipments, 'SUPPLY', 2,
                                                                   is_report_pdf,
                                                                   equipment_in_page)

                    toc_line_maker('AIR TERMINAL TEST SHEET', len(air_terminal_pages), 1)

                    vav_pages = vav_pages + air_terminal_pages

            return vav_pages

        while len(air_moving_equipments) > 2:
            current_air_moving_equipments = air_moving_equipments[:2]
            air_moving_equipments = air_moving_equipments[2:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_air_moving_equipments[0].sheetequipmentcommondata_set.get(
                    key__column_title__icontains='fan no.').value + ' & ' + current_air_moving_equipments[
                              1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(current_air_moving_equipments[0]),
                    fetch_air_moving_equipment_data(current_air_moving_equipments[1]),
                ]
            })
            toc_line_maker(current_air_moving_equipments[0].sheetequipmentcommondata_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + current_air_moving_equipments[
                               1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1)
            pages = pages + add_terminal_pages_for_air_moving(
                [current_air_moving_equipments[0], current_air_moving_equipments[1]])

            pages = pages + add_velocity([current_air_moving_equipments[0], current_air_moving_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving(
                [current_air_moving_equipments[0], current_air_moving_equipments[1]])
        if len(air_moving_equipments) == 2:
            pages.append({
                'type': 'AIRMOVING',
                'system': air_moving_equipments[0].sheetequipmentcommondata_set.get(
                    key__column_title__icontains='fan no.').value + ' & ' + air_moving_equipments[
                              1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(air_moving_equipments[0]),
                    fetch_air_moving_equipment_data(air_moving_equipments[1]),
                ]
            })
            toc_line_maker(air_moving_equipments[0].sheetequipmentcommondata_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + air_moving_equipments[
                               1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1)
            pages = pages + add_terminal_pages_for_air_moving([air_moving_equipments[0], air_moving_equipments[1]])

            pages = pages + add_velocity([air_moving_equipments[0], air_moving_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0], air_moving_equipments[1]])
        elif len(air_moving_equipments) == 1:
            pages.append({
                'type': 'AIRMOVING',
                'system': air_moving_equipments[0].sheetequipmentcommondata_set.get(
                    key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(air_moving_equipments[0]),
                ]
            })
            toc_line_maker(air_moving_equipments[0].sheetequipmentcommondata_set.get(
                key__column_title__icontains='fan no.').value,
                           0, 0, False)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1)
            pages = pages + add_terminal_pages_for_air_moving([air_moving_equipments[0]])

            pages = pages + add_velocity([air_moving_equipments[0]])

            pages = pages + add_vav_pages_using_air_moving([air_moving_equipments[0]])

        while len(exhaust_equipments) > 2:
            current_exhaust_equipments = exhaust_equipments[:2]
            exhaust_equipments = exhaust_equipments[2:]
            pages.append({
                'type': 'AIRMOVING',
                'system': current_exhaust_equipments[0].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value + ' & ' + current_exhaust_equipments[1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(current_exhaust_equipments[0]),
                    fetch_air_moving_equipment_data(current_exhaust_equipments[1]),
                ]
            })
            toc_line_maker(current_exhaust_equipments[0].sheetequipmentcommondata_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + current_exhaust_equipments[
                               1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1)
            pages = pages + add_terminal_pages_for_air_moving([current_exhaust_equipments[0], current_exhaust_equipments[1]])

            pages = pages + add_velocity([current_exhaust_equipments[0], current_exhaust_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([current_exhaust_equipments[0], current_exhaust_equipments[1]])
        if len(exhaust_equipments) == 2:
            pages.append({
                'type': 'AIRMOVING',
                'system': exhaust_equipments[0].sheetequipmentcommondata_set.get(
                    key__column_title__icontains='fan no.').value + ' & ' + exhaust_equipments[
                              1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(exhaust_equipments[0]),
                    fetch_air_moving_equipment_data(exhaust_equipments[1]),
                ]
            })
            toc_line_maker(exhaust_equipments[0].sheetequipmentcommondata_set.get(
                key__column_title__icontains='fan no.').value + ' & ' + exhaust_equipments[
                               1].sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
                           0, 0, False)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1)
            pages = pages + add_terminal_pages_for_air_moving([exhaust_equipments[0], exhaust_equipments[1]])

            pages = pages + add_velocity([exhaust_equipments[0], exhaust_equipments[1]])

            pages = pages + add_vav_pages_using_air_moving([exhaust_equipments[0], exhaust_equipments[1]])
        elif len(exhaust_equipments) == 1:
            pages.append({
                'type': 'AIRMOVING',
                'system': exhaust_equipments[0].sheetequipmentcommondata_set.get(
                    key__column_title__icontains='fan no.').value,
                'rows': [
                    fetch_air_moving_equipment_data(exhaust_equipments[0]),
                ]
            })
            toc_line_maker(exhaust_equipments[0].sheetequipmentcommondata_set.get(
                key__column_title__icontains='fan no.').value,
                           0, 0, False)
            toc_line_maker('AIR MOVING EQUIPMENT TEST SHEET', 1, 1)
            pages = pages + add_terminal_pages_for_air_moving([exhaust_equipments[0]])

            pages = pages + add_velocity([exhaust_equipments[0]])

            pages = pages + add_vav_pages_using_air_moving([exhaust_equipments[0]])

        if len(indipendent_vav_equipments) > 0:
            toc_line_maker('VAV\'S', 0, 0, False)
            pages = pages + add_independent_vav_pages(indipendent_vav_equipments)

        pages = pages + add_rogue_terminal_pages()

        pages = pages + add_pump_pages()

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
            'WEB_URL': WEB_URL,
            'STATIC_URL': STATIC_URL,
            'MEDIA_URL': MEDIA_URL,
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
            'WEB_URL': WEB_URL,
            'STATIC_URL': STATIC_URL,
            'MEDIA_URL': MEDIA_URL,
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
            'WEB_URL': WEB_URL,
            'MEDIA_URL': MEDIA_URL,
            'STATIC_URL': STATIC_URL,
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
    # s3.upload_file_to_bucket(file_name=file_path, key=s3_path)

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


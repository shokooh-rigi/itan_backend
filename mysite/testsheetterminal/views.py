import math
import os
import re
from itertools import chain
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from ..render import Render as PDFRender
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from django.db.models import Count
from django.db.models.functions import Cast, Coalesce
from django.http import JsonResponse
from django.db.models import Sum


footnote_indicator_choices = [
    ['1', '**'],
    ['2', 'N/A'],
]

# Create your views here.


@login_required
def terminal_sheet_list(request):
    search = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__icontains='terminal')
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "terminalList.html", parameters)


@login_required
def terminal_sheet_add(request):
    form = TerminalSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.filter(Q(datasheet__datasheetequipment__number_of_supply_air_terminal__gt=0) | Q(sheet__sheetequipment__number_of_supply_air_terminal__gt=0) | Q(sheet__sheetequipment__number_of_return_air_terminal__gt=0)).exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__icontains='terminal').values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='air terminal')
                sheet.save()
                return redirect('terminalSheetEquipmentList', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "terminalSheetAdd.html", parameters)


@login_required
def terminal_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    my_project = my_sheet.project
    vav_sheet_equipments = DataSheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='vav', sheet__project=my_project).filter(number_of_supply_air_terminal__gt=0)
    air_moving_sheet_equipments = SheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='air mov', sheet__project=my_project).filter(Q(number_of_supply_air_terminal__gt=0) | Q(number_of_return_air_terminal__gt=0) | Q(number_of_outside_air_terminal__gt=0) | Q(number_of_any_other__gt=0))
    vav_sheet_equipments = vav_sheet_equipments.filter(testsheetgeneraldata__value__icontains=project_name).order_by('terminal_design_data_entry_completed', 'terminal_actual_data_entry_completed', 'field_order').distinct()
    air_moving_sheet_equipments = air_moving_sheet_equipments.filter(sheetequipmentcommondata__value__icontains=project_name).order_by('terminal_design_data_entry_completed', 'terminal_actual_data_entry_completed', 'field_order').distinct()
    rogue_air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet, air_equipment__isnull=True, vav_equipment__isnull=True, type=4)
    parameters = {'air_moving_sheet_equipments': air_moving_sheet_equipments,
                  'vav_sheet_equipments': vav_sheet_equipments,
                  'rogue_air_terminal_equipments': len(rogue_air_terminal_equipments),
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "terminalSheetEquipmentsList.html", parameters)


@login_required
def terminal_sheet_others(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    rogue_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                           air_equipment__isnull=True,
                                                           vav_equipment__isnull=True,
                                                           type=4).values('equipment_name', 'other_group').annotate(dcount=Count('other_group')).order_by('other_group')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetEquipmentList', my_sheet.id)
        if request.POST.get("next"):

            AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                air_equipment__isnull=True,
                                                vav_equipment__isnull=True,
                                                type=4).delete()

            my_sheet.rogue_design_data_entry_completed = False
            my_sheet.rogue_actual_data_entry_completed = False
            my_sheet.save()

            field = 1
            while request.POST.get('extra-field-content-' + str(field)) and request.POST.get('extra-field-content-' + str(field)) != '':
                quantity = int(request.POST.get('extra-field-content-' + str(field)))
                name = request.POST.get('extra-field-title-' + str(field))
                for i in range(quantity):
                    new_terminal_equipment = AirTerminalEquipment(sheet=my_sheet,
                                                                  outlet_no=i+1,
                                                                  other_group=field,
                                                                  type=4,
                                                                  equipment_name=name)
                    new_terminal_equipment.save()
                field = field + 1
            return redirect('terminalSheetEquipmentList', my_sheet.id)


    parameters = {
        'rogue_equipments': rogue_equipments,
        'my_sheet': my_sheet,
        'sheet_id': sheet_id,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "terminalSheetOthers.html", parameters)


def fetch_sheet_equipment_data(this_sheet_equipment: AirTerminalEquipment, is_report_pdf: bool):
    if this_sheet_equipment.air_equipment:
        equipment_data = {
            'name': this_sheet_equipment.air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
            'outlet_no': this_sheet_equipment.outlet_no,
            'code': this_sheet_equipment.code
        }
    elif this_sheet_equipment.vav_equipment:
        equipment_data = {
            'name': this_sheet_equipment.vav_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value,
            'outlet_no': this_sheet_equipment.outlet_no,
            'code': this_sheet_equipment.code
        }
    else:
        equipment_data = {
            'name': this_sheet_equipment.equipment_name,
            'outlet_no': this_sheet_equipment.outlet_no,
            'code': this_sheet_equipment.code
        }

    design_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_design=True)
    design_data = [
        ('room_no', 'room no.'),
        ('size', 'size'),
        ('ak_factor', 'ak factor'),
        ('fpm', 'fpm'),
        ('cfm', 'cfm'),
        ('cfm_more', 'More info for CFM'),
        ('cfm_indicator', 'CFM Indicator'),
        ('cfm_note', 'CFM Note'),
    ]

    equipment_data['design'] = {}
    for key, val in design_data:
        design_field = design_fields.get(field_name__iexact=val)
        design_value = AirTerminalSheetData.objects.get(data_type=DataTypeChoices.Design.value, sheet_field=design_field,
                                                     air_terminal_equipment=this_sheet_equipment).value
        equipment_data['design'][key] = design_value

    if is_report_pdf:
        actual_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_actual=True)
        actual_data = [
            ('initial_fpm', 'initial fpm'),
            ('initial_cfm', 'initial cfm'),
            ('final_fpm', 'final fpm'),
            ('final_cfm', 'final cfm'),
            ('cfm_more', 'More info for CFM'),
            ('cfm_indicator', 'CFM Indicator'),
            ('cfm_note', 'CFM Note'),
            ('note', 'note'),
        ]
        equipment_data['actual'] = {}
        for key, val in actual_data:
            actual_field = actual_fields.get(field_name__iexact=val)
            actual_value = AirTerminalSheetData.objects.get(data_type=DataTypeChoices.Actual.value, sheet_field=actual_field,
                                                     air_terminal_equipment=this_sheet_equipment).value
            equipment_data['actual'][key] = actual_value

    return equipment_data


def get_pdf_empty_row():
    return {
        'name': '',
        'design': {
            'room_no': '',
            'outlet_no': '',
            'code': '',
            'size': '',
            'ak_factor': '',
            'fpm': '',
            'cfm': '',
        },
        'actual': {
            'initial_fpm': '',
            'initial_cfm': '',
            'final_fpm': '',
            'final_cfm': '',
            'note': '',
        },
    }


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def prepare_pdf_pages(equipment_list, page_type, airOrVav, is_report_pdf, equipment_in_page):
    pages = []
    design_total = 0
    initial_total = 0
    final_total = 0
    for equipment in equipment_list.all():
        cfm = equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Design.value, sheet_field__field_name__iexact='cfm').value
        if cfm:
            design_total += int(cfm)
        else:
            if airOrVav == 1:
                design_total = equipment.air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value
        if is_report_pdf:
            if equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='initial cfm').value != '':
                initial_total += int(equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='initial cfm').value)
            if equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='final cfm').value != '':
                final_total += int(equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='final cfm').value)
    if len(equipment_list) > (equipment_in_page - 1):
        equipments_data = []
        for equipment in equipment_list[0:equipment_in_page - 1]:
            equipments_data.append(fetch_sheet_equipment_data(equipment, is_report_pdf))
        pages.append({
            'type': page_type,
            'eq_name': equipment_list[0].equipment_name if airOrVav == 0 else '',
            'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value if airOrVav == 1 else equipment_list[0].vav_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value,
            'rows': [
                'title',
                equipments_data
            ]
        })
        remaining_rows = equipment_list[equipment_in_page:]
        while len(remaining_rows) > equipment_in_page:
            equipments_data = []
            for equipment in remaining_rows[0:equipment_in_page]:
                equipments_data.append(fetch_sheet_equipment_data(equipment, is_report_pdf))
            pages.append({
                'type': page_type,
            'eq_name': equipment_list[0].equipment_name if airOrVav == 0 else '',
                'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value if airOrVav == 1 else equipment_list[0].vav_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value,
                'rows': [
                    equipments_data
                ]
            })
            remaining_rows = remaining_rows[equipment_in_page + 1:]
        equipments_data = []
        for equipment in remaining_rows:
            equipments_data.append(fetch_sheet_equipment_data(equipment, is_report_pdf))
        pages.append({
            'type': page_type,
            'eq_name': equipment_list[0].equipment_name if airOrVav == 0 else '',
            'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value if airOrVav == 1 else equipment_list[0].vav_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value,
            'rows': [
                equipments_data,
                {
                    'd_cfm_total': design_total,
                    'i_cfm_total': initial_total,
                    'f_cfm_total': final_total,
                    'empty_rows': equipment_in_page - len(remaining_rows) - 1,
                }
            ]
        })
    else:
        equipments_data = []
        for equipment in equipment_list:
            equipments_data.append(fetch_sheet_equipment_data(equipment, is_report_pdf))

        pages.append({
            'type': page_type,
            'eq_name': equipment_list[0].equipment_name if airOrVav == 0 else '',
            'system': 'Rogue Terminals' if airOrVav == 0 else equipment_list[0].air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value if airOrVav == 1 else equipment_list[0].vav_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value,
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


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    air_sheet_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet, vav_equipment__isnull=True, air_equipment__terminal_design_data_entry_completed=True).order_by('air_equipment__field_order', 'air_equipment_id', 'type', 'outlet_no')
    vav_sheet_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet, air_equipment__isnull=True, vav_equipment__terminal_design_data_entry_completed=True).order_by('vav_equipment__field_order', 'vav_equipment_id', 'vav_equipment__field_order', 'outlet_no')

    if is_report_pdf:
        air_sheet_equipments = air_sheet_equipments.filter(air_equipment__terminal_actual_data_entry_completed=True)
        vav_sheet_equipments = vav_sheet_equipments.filter(vav_equipment__terminal_actual_data_entry_completed=True)

    # data = []
    # page = {'rows': [], 'system': ''}
    #
    # last_air_equipment = 0
    # last_air_equipment_type = 0
    # d_total = 0
    # i_total = 0
    # f_total = 0
    # eq_type = ''
    # eq_name = ''
    # i = 0
    equipment_in_page = 21
    # supply_lines = 0
    # return_lines = 0
    # outside_lines = 0
    # other_lines = 0

    pages = []

    last_air_equipment_id = 0
    value_list = air_sheet_equipments.values_list('air_equipment_id', flat=True).distinct()
    for value in value_list:
        if last_air_equipment_id != value:
            last_air_equipment_id = value
            all_air_equipment_terminals = air_sheet_equipments.filter(air_equipment_id=value)
            type_list = all_air_equipment_terminals.values_list('type', flat=True).distinct()
            group_by_terminal_type = {}
            for terminal_type in type_list:
                group_by_terminal_type[terminal_type] = all_air_equipment_terminals.filter(type=terminal_type)

            done_types = []
            for terminal_type in type_list:
                if terminal_type not in done_types:
                    if terminal_type == 1:
                        pages = pages + prepare_pdf_pages(group_by_terminal_type[1], 'SUPPLY', 1, is_report_pdf,
                                                          equipment_in_page)
                    elif terminal_type == 2:
                        pages = pages + prepare_pdf_pages(group_by_terminal_type[2], 'RETURN', 1, is_report_pdf,
                                                          equipment_in_page)
                    elif terminal_type == 3:
                        pages = pages + prepare_pdf_pages(group_by_terminal_type[3], 'OUTSIDE', 1, is_report_pdf,
                                                          equipment_in_page)
                    done_types.append(terminal_type)

    last_vav_equipment_id = 0
    value_list = vav_sheet_equipments.values_list('vav_equipment_id', flat=True).distinct()
    for value in value_list:
        if last_vav_equipment_id != value:
            last_vav_equipment_id = value
            all_supply_terminals = vav_sheet_equipments.filter(vav_equipment_id=value)

            pages = pages + prepare_pdf_pages(all_supply_terminals, 'SUPPLY', 2, is_report_pdf, equipment_in_page)


    # for air_equipment in air_sheet_equipments:
    #     if air_equipment.air_equipment.id != last_air_equipment or air_equipment.type != last_air_equipment_type:
    #         if last_air_equipment != 0:
    #             circle_time = equipment_in_page - ((i + supply_lines + return_lines + outside_lines + other_lines) % equipment_in_page)
    #             if air_equipment.air_equipment.id == last_air_equipment:
    #                 circle_time = 0
    #             else:
    #                 i = 0
    #                 supply_lines = 0
    #                 return_lines = 0
    #                 outside_lines = 0
    #                 other_lines = 0
    #             previous_general_data = {
    #                 'eq_name': eq_name,
    #                 'eq_type': eq_type,
    #                 'd_cfm_total': d_total,
    #                 'i_cfm_total': i_total,
    #                 'f_cfm_total': f_total,
    #                 'empty_rows': range(circle_time),
    #             }
    #             page['rows'][len(page['rows']) - 1].append(previous_general_data)
    #             d_total = 0
    #             i_total = 0
    #             f_total = 0
    #         if air_equipment.air_equipment.id != last_air_equipment and last_air_equipment != 0:
    #             page['system'] = eq_name
    #             data.append(page)
    #             page = {'rows': []}
    #         cfm_value = air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Design.value, sheet_field__field_name__iexact='cfm').value
    #         if cfm_value:
    #             d_total = int(cfm_value)
    #         if is_report_pdf:
    #             if air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='initial cfm').value != '':
    #                 i_total = int(air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='initial cfm').value)
    #             if air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='final cfm').value != '':
    #                 f_total = int(air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='final cfm').value)
    #         page['rows'].append([])
    #         last_air_equipment = air_equipment.air_equipment.id
    #         last_air_equipment_type = air_equipment.type
    #         if air_equipment.type == 1:
    #             eq_type = 'SUPPLY'
    #         elif air_equipment.type == 2:
    #             eq_type = 'RETURN'
    #         elif air_equipment.type == 3:
    #             eq_type = 'OUTSIDE'
    #         else:
    #             eq_type = air_equipment.equipment_name
    #         eq_name = air_equipment.air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value
    #     else:
    #         cfm_value = air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Design.value, sheet_field__field_name__iexact='cfm').value
    #         if cfm_value:
    #             d_total += int(cfm_value)
    #         if is_report_pdf:
    #             if air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='initial cfm').value != '':
    #                 i_total += int(air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                           sheet_field__field_name__iexact='initial cfm').value)
    #             if air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                           sheet_field__field_name__iexact='final cfm').value != '':
    #                 f_total += int(air_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value, sheet_field__field_name__iexact='final cfm').value)
    #
    #     page['rows'][len(page['rows']) - 1].append(fetch_sheet_equipment_data(air_equipment, is_report_pdf))
    #     i += 1
    #     if air_equipment.type == 1:
    #         supply_lines = 3
    #     elif air_equipment.type == 2:
    #         return_lines = 3
    #     elif air_equipment.type == 3:
    #         return_lines = 3
    #     else:
    #         other_lines += 3
    #
    # if air_sheet_equipments:
    #     group_total_pages = int((i + supply_lines + return_lines + outside_lines + other_lines) / equipment_in_page) + 1
    #     circle_time = equipment_in_page - ((i + supply_lines + return_lines + outside_lines + other_lines) % equipment_in_page)
    #     last_general_data = {
    #         'eq_name': eq_name,
    #         'eq_type': eq_type,
    #         'd_cfm_total': d_total,
    #         'i_cfm_total': i_total,
    #         'f_cfm_total': f_total,
    #         'empty_rows': range(circle_time),
    #     }
    #     page['rows'][len(page['rows']) - 1].append(last_general_data)
    #     page['system'] = eq_name
    #     data.append(page)



    # page = {'rows': []}
    #
    # last_vav_equipment = 0
    # d_total = 0
    # i_total = 0
    # f_total = 0
    # eq_type = 'SUPPLY'
    # eq_name = ''
    # i = 0
    # equipment_in_page = 23
    # for vav_equipment in vav_sheet_equipments:
    #     if vav_equipment.vav_equipment.id != last_vav_equipment:
    #         if last_vav_equipment != 0:
    #             circle_time = equipment_in_page - i - 3
    #             i = 0
    #             previous_general_data = {
    #                 'eq_name': eq_name,
    #                 'eq_type': eq_type,
    #                 'd_cfm_total': d_total,
    #                 'i_cfm_total': i_total,
    #                 'f_cfm_total': f_total,
    #                 'empty_rows': range(circle_time),
    #             }
    #             page['rows'][len(page['rows']) - 1].append(previous_general_data)
    #             d_total = 0
    #             i_total = 0
    #             f_total = 0
    #             i = 0
    #         if vav_equipment.vav_equipment.id != last_vav_equipment and last_vav_equipment != 0:
    #             page['system'] = eq_name
    #             data.append(page)
    #             page = {'rows': []}
    #         d_total = int(vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Design.value,
    #                                                                  sheet_field__field_name__iexact='cfm').value)
    #         if is_report_pdf:
    #             if vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                      sheet_field__field_name__iexact='initial cfm').value != '':
    #                 i_total = int(vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                      sheet_field__field_name__iexact='initial cfm').value)
    #             if vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                      sheet_field__field_name__iexact='final cfm').value != '':
    #                 f_total = int(vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                      sheet_field__field_name__iexact='final cfm').value)
    #         page['rows'].append([])
    #         last_vav_equipment = vav_equipment.vav_equipment.id
    #         eq_name = vav_equipment.vav_equipment.testsheetgeneraldata_set.get(
    #             key__column_title__icontains='code').value
    #     else:
    #         d_total += int(vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Design.value,
    #                                                                   sheet_field__field_name__iexact='cfm').value)
    #         if is_report_pdf:
    #             if vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                           sheet_field__field_name__iexact='initial cfm').value != '':
    #                 i_total += int(vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                       sheet_field__field_name__iexact='initial cfm').value)
    #             if vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                           sheet_field__field_name__iexact='final cfm').value != '':
    #                 f_total += int(vav_equipment.airterminalsheetdata_set.get(data_type=DataTypeChoices.Actual.value,
    #                                                                       sheet_field__field_name__iexact='final cfm').value)
    #
    #     page['rows'][len(page['rows']) - 1].append(fetch_sheet_equipment_data(vav_equipment, is_report_pdf))
    #     i += 1
    #
    # if vav_sheet_equipments:
    #     circle_time = equipment_in_page - i - 3
    #     last_general_data = {
    #         'eq_name': eq_name,
    #         'eq_type': eq_type,
    #         'd_cfm_total': d_total,
    #         'i_cfm_total': i_total,
    #         'f_cfm_total': f_total,
    #         'empty_rows': range(circle_time),
    #     }
    #     page['rows'][len(page['rows']) - 1].append(last_general_data)
    #     page['system'] = eq_name
    #
    #     data.append(page)

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
        # 'form': {
        #     'my_sheet': my_sheet,
        #     'data': data,
        # },
        'pages': pages,
        'file_name': 'Air Terminal Test Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
        'WEB_URL': WEB_URL,
        'STATIC_URL': STATIC_URL,
        'MEDIA_URL': MEDIA_URL,
        'os': system(),
    }


@login_required
def equipments_generate_tech_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, False)
    pdf_type = 'terminalEquipmentReport'
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/terminalSheetEquipmentTechTemplate.html', parameters, pdf_type)
    # if os.path.exists(pdf_path):
    #     with open(pdf_path, 'rb') as fh:
    #         response = HttpResponse(fh.read(), content_type="application/pdf")
    #         response['Content-Disposition'] = 'inline; filename=' + pdf_name
    #         return response
    # else:
    #     return 'error'
    sending_parameters = {
        'pdf_type': pdf_type,
        'pdf_name': pdf_name,
        'pdf_path': pdf_path,
    }
    return JsonResponse(sending_parameters)


@login_required
def equipments_generate_report_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, True)
    pdf_type = 'terminalEquipmentReport'
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/terminalSheetEquipmentTemplate.html', parameters,
                                                  'terminalEquipmentReport')

    sending_parameters = {
        'pdf_type': pdf_type,
        'pdf_name': pdf_name,
        'pdf_path': pdf_path,
    }
    return JsonResponse(sending_parameters)


def split(value: str, sep: str):
    return value.replace(' ', '').split(sep)


def contains(value: str, sub: str):
    return value.find(sub) != -1


def check_form_values(request, this_sheet_equipment: AirTerminalEquipment, is_design_form: bool):
    is_actual_form = not is_design_form

    design_field_regex = re.compile(r'\[field-[\d]+-design]', re.I)
    actual_field_regex = re.compile(r'\[field-[\d]+-actual]', re.I)
    design_field_name_prefix = 'company_value_'
    actual_field_name_prefix = 'actual_value_'

    test_sheet_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set
    test_sheet_operations = this_sheet_equipment.sheet.test_sheet_type.testsheetoperation_set
    design_fields = test_sheet_fields.filter(show_in_design=True)

    if is_design_form:
        field_regex = design_field_regex
        field_name_prefix = design_field_name_prefix
        form_fields = test_sheet_fields.filter(show_in_design=True)
        custom_operations = test_sheet_operations.filter(apply_on_design=True)
    else:
        field_regex = actual_field_regex
        field_name_prefix = actual_field_name_prefix
        form_fields = test_sheet_fields.filter(show_in_actual=True)
        custom_operations = test_sheet_operations.filter(apply_on_actual=True)

    def replace_design_values(expression, expression_msg):
        def get_design_value(m):
            field_id = m.group()[7:-8]
            actual_value = request.POST.get(f'{actual_field_name_prefix}{field_id}')
            design_field = design_fields.get(pk=field_id)
            if this_sheet_equipment.equipment:
                design_value = EquipmentDbDesignData.objects.get(equipment=this_sheet_equipment.equipment,
                                                                 key=design_field).value
            else:
                design_value = TestSheetData.objects.get(data_type=DataTypeChoices.Design.value,
                                                         sheet_field=design_field,
                                                         sheet_equipment=this_sheet_equipment).value
            return find_closest_design_value(actual_value, design_value, '-')

        expression = re.sub(design_field_regex, get_design_value, expression)
        expression_msg = re.sub(design_field_regex,
                                lambda m: design_fields.get(pk=m.group()[7:-8]).field_name + ' (design)',
                                expression_msg)
        return expression, expression_msg

    # validate field value range
    conv_to_num = None
    for field in form_fields:
        if field.field_type == FieldTypeChoices.Characters.value:
            continue
        elif field.field_type == FieldTypeChoices.Integer.value:
            conv_to_num = int
        elif field.field_type == FieldTypeChoices.Float.value:
            conv_to_num = float

        if request.POST.get(f'{field_name_prefix}{field.id}'):
            try:
                form_field_value = conv_to_num(request.POST.get(f'{field_name_prefix}{field.id}'))
            except ValueError:
                print(ValueError)
                return f'{field.field_name} value is not valid. The value must be ' \
                       f'{"integer" if conv_to_num == int else "float"} number.'

            if field.field_range_or_selective == FieldRangeOrSelectiveChoices.Range.value:
                field_range = split(field.field_range, '-')
                min_value = conv_to_num(field_range[0])
                max_value = conv_to_num(field_range[1])
                if form_field_value < min_value or max_value < form_field_value:
                    return f'{field.field_name} value is not in range. Valid range is {field.field_range}.'
            elif field.field_range_or_selective == FieldRangeOrSelectiveChoices.Selective.value:
                field_range = split(field.field_range, ',')
                if form_field_value not in map(lambda x: conv_to_num(x), field_range):
                    return f'{field.field_name} value is not selected right. Valid choices are {field.field_range}.'

    # check custom operations
    custom_operations = custom_operations.filter(~Q(operand_type=OperandChoices.AssignTo.value))
    for custom_operation in custom_operations:
        left_side = left_side_msg = custom_operation.operation.strip().lower()
        right_side = right_side_msg = custom_operation.result_field.strip().lower()

        # ignore custom_operation when:
        #
        #                               | left_side has 'actual' word
        #       | is_design_form and ---  OR
        #       |                       | right_side does not matches [field-ID-design]
        # if ---  OR
        #       |
        #       | is_actual_form and right_side does not matches [field-ID-actual]
        #
        if (is_design_form and (contains(left_side, 'actual') or not re.fullmatch(design_field_regex, right_side))) or \
                (is_actual_form and not re.fullmatch(actual_field_regex, right_side)):
            continue

        try:
            # if is_design_form then replace design fields in formula with their form values
            # else if is_actual_form then replace actual fields in formula with their form values
            left_side = re.sub(field_regex, lambda m: request.POST.get(f'{field_name_prefix}{m.group()[7:-8]}'),
                               left_side)
            left_side_msg = re.sub(field_regex, lambda m: form_fields.get(pk=m.group()[7:-8]).field_name, left_side_msg)
            right_side = request.POST.get(f'{field_name_prefix}{right_side[7:-8]}')
            right_side_msg = form_fields.get(pk=right_side_msg[7:-8]).field_name

            # when is_actual_form and the formula has design fields
            # replace design fields in the formula with design values previously saved in the database
            if is_actual_form and contains(left_side, 'design'):
                left_side, left_side_msg = replace_design_values(left_side, left_side_msg)

            left_side = eval(left_side)
            right_side = eval(right_side)
            if custom_operation.operand_type == OperandChoices.EqualTo.value:
                if left_side != right_side:
                    return f'{left_side_msg} must be equal to {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.GreaterThan.value:
                if left_side <= right_side:
                    return f'{left_side_msg} must be greater than {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.GreaterOrEqualTo.value:
                if left_side < right_side:
                    return f'{left_side_msg} must be greater than or equal to {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.SmallerThan.value:
                if left_side >= right_side:
                    return f'{left_side_msg} must be smaller than {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.SmallerOrEqualTo.value:
                if left_side > right_side:
                    return f'{left_side_msg} must be smaller than or equal to {right_side_msg}'
        except:
            continue

    return None


def manual_replace(s, char, index):
    return s[:index] + char + s[index +1:]


@login_required
def terminal_sheet_equipment_design_data(request, sheet_id, sheet_equipment_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    is_air_moving = SheetEquipment.objects.filter(id=sheet_equipment_id, sheet__project_id=my_sheet.project.id)
    if is_air_moving:
        equipment_type = 1
        this_sheet_equipment = get_object_or_404(SheetEquipment, id=sheet_equipment_id)
        sheet_code = this_sheet_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value
    else:
        equipment_type = 2
        this_sheet_equipment = get_object_or_404(DataSheetEquipment, id=sheet_equipment_id)
        sheet_code = this_sheet_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value
    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains='terminal')
    supply_repeat_list = []
    return_repeat_list = []
    outside_repeat_list = []
    other_repeat_list = []
    return_repeat_num = 0
    outside_repeat_num = 0
    other_repeat_num = 0
    supply_repeat_num = this_sheet_equipment.number_of_supply_air_terminal
    for i in range(0, supply_repeat_num):
        supply_repeat_list.append(i)
    if is_air_moving:
        return_repeat_num = this_sheet_equipment.number_of_return_air_terminal
        outside_repeat_num = this_sheet_equipment.number_of_outside_air_terminal
        other_repeat_num = this_sheet_equipment.number_of_any_other
        for i in range(0, return_repeat_num):
            return_repeat_list.append(i)
        for i in range(0, outside_repeat_num):
            outside_repeat_list.append(i)
        for i in range(0, other_repeat_num):
            other_repeat_list.append(i)
    codes = AirTerminalCode.objects.filter(is_custom=False)

    for i in range(supply_repeat_num):
        i += 1
        if is_air_moving:
            air_terminal_eq_result = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         air_equipment=this_sheet_equipment,
                                                                         outlet_no=i,
                                                                         type=1).count()
            if air_terminal_eq_result == 0:
                new_terminal_equipment = AirTerminalEquipment(sheet=my_sheet,
                                                              air_equipment=this_sheet_equipment, outlet_no=i, type=1)
                new_terminal_equipment.save()

        else:
            air_terminal_eq_result = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         vav_equipment=this_sheet_equipment,
                                                                         outlet_no=i,
                                                                         type=1).count()
            if air_terminal_eq_result == 0:
                new_terminal_equipment = AirTerminalEquipment(sheet=my_sheet,
                                                              vav_equipment=this_sheet_equipment, outlet_no=i, type=1)
                new_terminal_equipment.save()

    for i in range(return_repeat_num):
        i += 1
        air_terminal_eq_result = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                     air_equipment=this_sheet_equipment,
                                                                     outlet_no=i,
                                                                     type=2).count()
        if air_terminal_eq_result == 0:
            new_terminal_equipment = AirTerminalEquipment(sheet=my_sheet, air_equipment=this_sheet_equipment,
                                                          outlet_no=i, type=2)
            new_terminal_equipment.save()

    for i in range(outside_repeat_num):
        i += 1
        air_terminal_eq_result = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                     air_equipment=this_sheet_equipment,
                                                                     outlet_no=i,
                                                                     type=3).count()
        if air_terminal_eq_result == 0:
            new_terminal_equipment = AirTerminalEquipment(sheet=my_sheet, air_equipment=this_sheet_equipment,
                                                          outlet_no=i, type=3)
            new_terminal_equipment.save()


    for i in range(other_repeat_num):
        i += 1
        air_terminal_eq_result = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                     air_equipment=this_sheet_equipment,
                                                                     outlet_no=i,
                                                                     type=4).count()
        if air_terminal_eq_result == 0:
            new_terminal_equipment = AirTerminalEquipment(sheet=my_sheet, air_equipment=this_sheet_equipment,
                                                          outlet_no=i, type=4)
            new_terminal_equipment.save()

    if is_air_moving:
        supply_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         air_equipment=this_sheet_equipment,
                                                                         type=1).order_by('outlet_no')
        return_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         air_equipment=this_sheet_equipment,
                                                                         type=2).order_by('outlet_no')
        outside_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          air_equipment=this_sheet_equipment,
                                                                          type=3).order_by('outlet_no')
        other_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          air_equipment=this_sheet_equipment,
                                                                          type=4).order_by('outlet_no')
    else:
        supply_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         vav_equipment=this_sheet_equipment,
                                                                         type=1).order_by('outlet_no')
        return_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         vav_equipment=this_sheet_equipment,
                                                                         type=2).order_by('outlet_no')
        outside_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         vav_equipment=this_sheet_equipment,
                                                                         type=3).order_by('outlet_no')
        other_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          vav_equipment=this_sheet_equipment,
                                                                          type=4).order_by('outlet_no')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetEquipmentList', my_sheet.id)
        if request.POST.get("next"):
            error_msg = None
            if error_msg is not None:
                parameters = {
                    'this_sheet_equipment': this_sheet_equipment,
                    'equipment_type': equipment_type,
                    'design_fields': design_fields,
                    'error_msg': error_msg,
                    'sheet_code': sheet_code,
                    'supply_repeat_list': supply_repeat_list,
                    'return_repeat_list': return_repeat_list,
                    'outside_repeat_list': outside_repeat_list,
                    'other_repeat_list': other_repeat_list,
                    'codes': codes,
                    'indicator_choices': footnote_indicator_choices,
                }
                return render(request, "terminalSheetEquipmentDesignData.html", parameters)

            # if no error save design values
            for supply_terminal_equipment in supply_terminal_equipments:
                new_code = request.POST.get(f'supply_code_select_{supply_terminal_equipment.id}')
                size_type = AirTerminalCode.objects.get(id=new_code).size_type
                AirTerminalEquipment.objects.filter(id=supply_terminal_equipment.id).update(code=new_code)
                for design_field in design_fields:
                    if design_field.field_name.lower() == 'size':
                        if size_type == 1:
                            new_value = request.POST.get(f'supply_company_value_{design_field.id}_{supply_terminal_equipment.id}')
                            new_value = new_value + '"'
                        elif size_type == 2:
                            new_val_x = str(request.POST.get(f'supply_company_value_{design_field.id}_{supply_terminal_equipment.id}-x'))
                            new_val_y = str(request.POST.get(f'supply_company_value_{design_field.id}_{supply_terminal_equipment.id}-y'))
                            new_value = new_val_x + ' X ' + new_val_y
                    else:
                        if design_field.field_type == 4:
                            if request.POST.get(f'supply_company_value_{design_field.id}_{supply_terminal_equipment.id}'):
                                new_value = True
                            else:
                                new_value = False
                        else:
                            new_value = request.POST.get(f'supply_company_value_{design_field.id}_{supply_terminal_equipment.id}').strip()
                            print(new_value)
                    num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                      air_terminal_equipment=supply_terminal_equipment,
                                                                      sheet_field=design_field).count()

                    if num_results > 0:
                        AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                      air_terminal_equipment=supply_terminal_equipment,
                                                                      sheet_field=design_field).update(value=new_value)
                    else:
                        new_object = AirTerminalSheetData(data_type=DataTypeChoices.Design.value,
                                                          air_terminal_equipment=supply_terminal_equipment,
                                                          sheet_field=design_field,
                                                          value=new_value)
                        new_object.save()

            if is_air_moving:
                for return_terminal_equipment in return_terminal_equipments:
                    new_code = request.POST.get(f'return_code_select_{return_terminal_equipment.id}')
                    size_type = AirTerminalCode.objects.get(id=new_code).size_type
                    AirTerminalEquipment.objects.filter(id=return_terminal_equipment.id).update(code=new_code)
                    for design_field in design_fields:
                        if design_field.field_name.lower() == 'size':
                            if size_type == 1:
                                new_value = request.POST.get(f'return_company_value_{design_field.id}_{return_terminal_equipment.id}')
                                new_value = new_value + '"'
                            elif size_type == 2:
                                new_val_x = request.POST.get(f'return_company_value_{design_field.id}_{return_terminal_equipment.id}-x').strip()
                                new_val_y = request.POST.get(f'return_company_value_{design_field.id}_{return_terminal_equipment.id}-y').strip()
                                new_value = new_val_x + ' X ' + new_val_y
                        else:
                            if design_field.field_type == 4:
                                if request.POST.get(
                                        f'return_company_value_{design_field.id}_{return_terminal_equipment.id}'):
                                    new_value = True
                                else:
                                    new_value = False
                            else:
                                new_value = request.POST.get(
                                    f'return_company_value_{design_field.id}_{return_terminal_equipment.id}').strip()

                        num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                          air_terminal_equipment=return_terminal_equipment,
                                                                          sheet_field=design_field).count()

                        if num_results > 0:
                            AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                air_terminal_equipment=return_terminal_equipment,
                                                                sheet_field=design_field).update(value=new_value)
                        else:
                            new_object = AirTerminalSheetData(data_type=DataTypeChoices.Design.value,
                                                              air_terminal_equipment=return_terminal_equipment,
                                                              sheet_field=design_field,
                                                              value=new_value)
                            new_object.save()

                for outside_terminal_equipment in outside_terminal_equipments:
                    new_code_text = request.POST.get(f'outside_code_select_{outside_terminal_equipment.id}')
                    code_result = AirTerminalCode.objects.filter(name=new_code_text, is_custom=True).count()
                    if code_result > 0:
                        new_code = AirTerminalCode.objects.get(name=new_code_text, is_custom=True)
                    else:
                        new_code = AirTerminalCode(name=new_code_text, is_custom=True)
                        new_code.save()
                    AirTerminalEquipment.objects.filter(id=outside_terminal_equipment.id).update(code=new_code.pk)
                    for design_field in design_fields:
                        if design_field.field_name.lower() == 'size':
                            new_value = request.POST.get(
                                f'outside_company_value_{design_field.id}_{outside_terminal_equipment.id}').strip()
                            new_value = new_value + '"'
                        else:
                            if design_field.field_type == 4:
                                if request.POST.get(
                                        f'outside_company_value_{design_field.id}_{outside_terminal_equipment.id}'):
                                    new_value = True
                                else:
                                    new_value = False
                            else:
                                new_value = request.POST.get(
                                    f'outside_company_value_{design_field.id}_{outside_terminal_equipment.id}').strip()

                        num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                          air_terminal_equipment=outside_terminal_equipment,
                                                                          sheet_field=design_field).count()

                        if num_results > 0:
                            AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                air_terminal_equipment=outside_terminal_equipment,
                                                                sheet_field=design_field).update(value=new_value)
                        else:
                            new_object = AirTerminalSheetData(data_type=DataTypeChoices.Design.value,
                                                              air_terminal_equipment=outside_terminal_equipment,
                                                              sheet_field=design_field,
                                                              value=new_value)
                            new_object.save()

            this_sheet_equipment.terminal_design_data_entry_completed = True
            this_sheet_equipment.save()

            return redirect('terminalSheetEquipmentList', my_sheet.id)
    parameters = {
        'this_sheet_equipment': this_sheet_equipment,
        'equipment_type': equipment_type,
        'design_fields': design_fields,
        'sheet_code': sheet_code,
        'my_sheet': my_sheet,
        'supply_repeat_list': supply_repeat_list,
        'return_repeat_list': return_repeat_list,
        'outside_repeat_list': outside_repeat_list,
        'other_repeat_list': other_repeat_list,
        'codes': codes,
        'supply_terminal_equipments': supply_terminal_equipments,
        'return_terminal_equipments': return_terminal_equipments,
        'outside_terminal_equipments': outside_terminal_equipments,
        'other_equipments': other_equipments,
        'indicator_choices': footnote_indicator_choices,
    }
    return render(request, "terminalSheetEquipmentDesignData.html", parameters)


@login_required
def rogue_design_data(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains='terminal')

    rogue_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                           air_equipment__isnull=True,
                                                           vav_equipment__isnull=True,
                                                           type=4).order_by('other_group')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetEquipmentList', my_sheet.id)
        if request.POST.get("next"):
            for rogue_equipment in rogue_equipments:
                new_code_text = request.POST.get(f'other_code_select_{rogue_equipment.id}')
                eq_name = request.POST.get(f'other_name_{rogue_equipment.id}')
                code_result = AirTerminalCode.objects.filter(name=new_code_text, is_custom=True).count()
                if code_result > 0:
                    new_code = AirTerminalCode.objects.get(name=new_code_text, is_custom=True)
                else:
                    new_code = AirTerminalCode(name=new_code_text, is_custom=True)
                    new_code.save()
                AirTerminalEquipment.objects.filter(id=rogue_equipment.id).update(code=new_code.pk)
                AirTerminalEquipment.objects.filter(id=rogue_equipment.id).update(equipment_name=eq_name)
                for design_field in design_fields:
                    if design_field.field_type == 4:
                        if request.POST.get(
                                f'other_company_value_{design_field.id}_{rogue_equipment.id}'):
                            new_value = True
                        else:
                            new_value = False
                    else:
                        new_value = request.POST.get(
                            f'other_company_value_{design_field.id}_{rogue_equipment.id}').strip()

                    num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                                      air_terminal_equipment=rogue_equipment,
                                                                      sheet_field=design_field).count()

                    if num_results > 0:
                        AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                            air_terminal_equipment=rogue_equipment,
                                                            sheet_field=design_field).update(value=new_value)
                    else:
                        new_object = AirTerminalSheetData(data_type=DataTypeChoices.Design.value,
                                                          air_terminal_equipment=rogue_equipment,
                                                          sheet_field=design_field,
                                                          value=new_value)
                        new_object.save()
            my_sheet.rogue_design_data_entry_completed = True
            my_sheet.save()

            return redirect('terminalSheetEquipmentList', my_sheet.id)
    parameters = {
        'design_fields': design_fields,
        'my_sheet': my_sheet,
        'rogue_equipments': rogue_equipments,
    }
    return render(request, "rogueEquipmentDesignData.html", parameters)


@login_required
def terminal_sheet_equipment_actual_data(request, sheet_id, sheet_equipment_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    is_air_moving = SheetEquipment.objects.filter(id=sheet_equipment_id, sheet__project_id=my_sheet.project.id)
    if is_air_moving:
        equipment_type = 1
        this_sheet_equipment = get_object_or_404(SheetEquipment, id=sheet_equipment_id)
        sheet_code = this_sheet_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value
    else:
        equipment_type = 2
        this_sheet_equipment = get_object_or_404(DataSheetEquipment, id=sheet_equipment_id)
        sheet_code = this_sheet_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value
    supply_repeat_list = []
    return_repeat_list = []
    outside_repeat_list = []
    other_repeat_list = []
    return_repeat_num = 0
    other_repeat_num = 0
    outside_repeat_num = 0
    supply_repeat_num = this_sheet_equipment.number_of_supply_air_terminal
    for i in range(0, supply_repeat_num):
        supply_repeat_list.append(i)
    if is_air_moving:
        return_repeat_num = this_sheet_equipment.number_of_return_air_terminal
        for i in range(0, return_repeat_num):
            return_repeat_list.append(i)
        outside_repeat_num = this_sheet_equipment.number_of_outside_air_terminal
        for i in range(0, outside_repeat_num):
            outside_repeat_list.append(i)
        other_repeat_num = this_sheet_equipment.number_of_any_other
        for i in range(0, other_repeat_num):
            other_repeat_list.append(i)
    codes = AirTerminalCode.objects.filter(is_custom=False)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='terminal')

    if is_air_moving:
        supply_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         air_equipment=this_sheet_equipment,
                                                                         type=1).order_by('outlet_no')
        return_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         air_equipment=this_sheet_equipment,
                                                                         type=2).order_by('outlet_no')
        outside_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          air_equipment=this_sheet_equipment,
                                                                          type=3).order_by('outlet_no')
        other_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          air_equipment=this_sheet_equipment,
                                                                          type=4).order_by('outlet_no')
    else:
        supply_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         vav_equipment=this_sheet_equipment,
                                                                         type=1).order_by('outlet_no')
        return_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                         vav_equipment=this_sheet_equipment,
                                                                         type=2).order_by('outlet_no')
        outside_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          vav_equipment=this_sheet_equipment,
                                                                          type=3).order_by('outlet_no')
        other_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                                          vav_equipment=this_sheet_equipment,
                                                                          type=4).order_by('outlet_no')

    ak_factor_field_id = TestSheetField.objects.get(field_name__iexact='AK Factor').id

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetEquipmentList', my_sheet.id)
        if request.POST.get("next"):
            # error_msg = check_form_values(request, my_sheet, False)
            error_msg = None
            if error_msg is not None:
                parameters = {
                    'this_sheet_equipment': this_sheet_equipment,
                    'equipment_type': equipment_type,
                    'actual_fields': actual_fields,
                    'sheet_code': sheet_code,
                    'my_sheet': my_sheet,
                    'supply_repeat_list': supply_repeat_list,
                    'return_repeat_list': return_repeat_list,
                    'outside_repeat_list': outside_repeat_list,
                    'other_repeat_list': other_repeat_list,
                    'codes': codes,
                    'supply_terminal_equipments': supply_terminal_equipments,
                    'return_terminal_equipments': return_terminal_equipments,
                    'outside_terminal_equipments': outside_terminal_equipments,
                    'other_equipments': other_equipments,
                    'indicator_choices': footnote_indicator_choices,
                    'error_msg': error_msg,
                }
                return render(request, "terminalSheetEquipmentActualData.html", parameters)

            for supply_terminal_equipment in supply_terminal_equipments:
                for actual_field in actual_fields:
                    if actual_field.field_type == 4:
                        new_value = True if request.POST.get(f'supply_actual_value_{actual_field.id}_{supply_terminal_equipment.id}') else False
                    else:
                        new_value = request.POST.get(f'supply_actual_value_{actual_field.id}_{supply_terminal_equipment.id}').strip()

                    num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                      air_terminal_equipment=supply_terminal_equipment,
                                                                      sheet_field=actual_field).count()

                    if num_results > 0:
                        AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                            air_terminal_equipment=supply_terminal_equipment,
                                                            sheet_field=actual_field).update(value=new_value)
                    else:
                        new_object = AirTerminalSheetData(data_type=DataTypeChoices.Actual.value,
                                                          air_terminal_equipment=supply_terminal_equipment,
                                                          sheet_field=actual_field,
                                                          value=new_value)
                        new_object.save()

            if is_air_moving:
                for return_terminal_equipment in return_terminal_equipments:
                    for actual_field in actual_fields:
                        if actual_field.field_type == 4:
                            new_value = True if request.POST.get(
                                f'return_actual_value_{actual_field.id}_{return_terminal_equipment.id}') else False
                        else:
                            new_value = request.POST.get(
                                f'return_actual_value_{actual_field.id}_{return_terminal_equipment.id}').strip()

                        num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                          air_terminal_equipment=return_terminal_equipment,
                                                                          sheet_field=actual_field).count()

                        if num_results > 0:
                            AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                air_terminal_equipment=return_terminal_equipment,
                                                                sheet_field=actual_field).update(value=new_value)
                        else:
                            new_object = AirTerminalSheetData(data_type=DataTypeChoices.Actual.value,
                                                              air_terminal_equipment=return_terminal_equipment,
                                                              sheet_field=actual_field,
                                                              value=new_value)
                            new_object.save()

                for outside_terminal_equipment in outside_terminal_equipments:
                    for actual_field in actual_fields:
                        if actual_field.field_type == 4:
                            new_value = True if request.POST.get(
                                f'supply_actual_value_{actual_field.id}_{supply_terminal_equipment.id}') else False
                        else:
                            new_value = request.POST.get(
                                f'outside_actual_value_{actual_field.id}_{outside_terminal_equipment.id}').strip()

                        num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                          air_terminal_equipment=outside_terminal_equipment,
                                                                          sheet_field=actual_field).count()

                        if num_results > 0:
                            AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                air_terminal_equipment=outside_terminal_equipment,
                                                                sheet_field=actual_field).update(value=new_value)
                        else:
                            new_object = AirTerminalSheetData(data_type=DataTypeChoices.Actual.value,
                                                              air_terminal_equipment=outside_terminal_equipment,
                                                              sheet_field=actual_field,
                                                              value=new_value)
                            new_object.save()

                for other_equipment in other_equipments:
                    for actual_field in actual_fields:
                        if actual_field.field_type == 4:
                            new_value = True if request.POST.get(
                                f'supply_actual_value_{actual_field.id}_{supply_terminal_equipment.id}') else False
                        else:
                            if request.POST.get(f'other_actual_value_{actual_field.id}_{other_equipment.id}'):
                                new_value = request.POST.get(f'other_actual_value_{actual_field.id}_{other_equipment.id}').strip()
                            else:
                                new_value = ''

                        num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                          air_terminal_equipment=other_equipment,
                                                                          sheet_field=actual_field).count()

                        if num_results > 0:
                            AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                air_terminal_equipment=other_equipment,
                                                                sheet_field=actual_field).update(value=new_value)
                        else:
                            new_object = AirTerminalSheetData(data_type=DataTypeChoices.Actual.value,
                                                              air_terminal_equipment=other_equipment,
                                                              sheet_field=actual_field,
                                                              value=new_value)
                            new_object.save()
            this_sheet_equipment.terminal_actual_data_entry_completed = True
            this_sheet_equipment.save()
            return redirect('terminalSheetEquipmentList', my_sheet.id)

    parameters = {
        'this_sheet_equipment': this_sheet_equipment,
        'equipment_type': equipment_type,
        'actual_fields': actual_fields,
        'sheet_code': sheet_code,
        'my_sheet': my_sheet,
        'supply_repeat_list': supply_repeat_list,
        'return_repeat_list': return_repeat_list,
        'outside_repeat_list': outside_repeat_list,
        'other_repeat_list': other_repeat_list,
        'codes': codes,
        'supply_terminal_equipments': supply_terminal_equipments,
        'return_terminal_equipments': return_terminal_equipments,
        'outside_terminal_equipments': outside_terminal_equipments,
        'other_equipments': other_equipments,
        'ak_factor_field_id': ak_factor_field_id,
        'indicator_choices': footnote_indicator_choices,
    }
    return render(request, "terminalSheetEquipmentActualData.html", parameters)


@login_required
def rogue_actual_data(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='terminal')

    rogue_equipments = AirTerminalEquipment.objects.filter(sheet=my_sheet,
                                                           air_equipment__isnull=True,
                                                           vav_equipment__isnull=True,
                                                           type=4).order_by('other_group')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetEquipmentList', my_sheet.id)
        if request.POST.get("next"):
            for rogue_equipment in rogue_equipments:
                for actual_field in actual_fields:
                    if actual_field.field_type == 4:
                        new_value = True if request.POST.get(
                            f'supply_actual_value_{actual_field.id}_{rogue_equipment.id}') else False
                    else:
                        new_value = request.POST.get(
                            f'other_actual_value_{actual_field.id}_{rogue_equipment.id}').strip()

                    num_results = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                                      air_terminal_equipment=rogue_equipment,
                                                                      sheet_field=actual_field).count()

                    if num_results > 0:
                        AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                            air_terminal_equipment=rogue_equipment,
                                                            sheet_field=actual_field).update(value=new_value)
                    else:
                        new_object = AirTerminalSheetData(data_type=DataTypeChoices.Actual.value,
                                                          air_terminal_equipment=rogue_equipment,
                                                          sheet_field=actual_field,
                                                          value=new_value)
                        new_object.save()
            my_sheet.rogue_actual_data_entry_completed = True
            my_sheet.save()

            return redirect('terminalSheetEquipmentList', my_sheet.id)
    parameters = {
        'actual_fields': actual_fields,
        'my_sheet': my_sheet,
        'rogue_equipments': rogue_equipments,
    }
    return render(request, "rogueEquipmentActualData.html", parameters)


@login_required
def terminal_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('terminalSheetHome')
        if request.POST.get("confirm"):
            this_project = this_sheet.project
            infected_data_sheet_equipments = DataSheetEquipment.objects.filter(sheet__project=this_project,
                                                                               number_of_supply_air_terminal__gt=0)
            for infected_data_sheet_equipment in infected_data_sheet_equipments:
                infected_data_sheet_equipment.terminal_design_data_entry_completed = False
                infected_data_sheet_equipment.terminal_actual_data_entry_completed = False
                infected_data_sheet_equipment.save()
            infected_data_sheet_equipments = SheetEquipment.objects.filter(sheet__project=this_project)\
                .filter(Q(number_of_supply_air_terminal__gt=0) | Q(number_of_return_air_terminal__gt=0))
            for infected_data_sheet_equipment in infected_data_sheet_equipments:
                infected_data_sheet_equipment.terminal_design_data_entry_completed = False
                infected_data_sheet_equipment.terminal_actual_data_entry_completed = False
                infected_data_sheet_equipment.save()
            all_air_terminal_equipments = AirTerminalEquipment.objects.filter(sheet=this_sheet)
            for air_terminal_equipment in all_air_terminal_equipments:
                air_terminal_equipment.delete()
            this_sheet.delete()
            return redirect('terminalSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "terminalSheetDelete.html", parameters)

import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
import urllib.request as url_request
from django.http import HttpResponse
from .models import DataSheet
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mysite.utils.pdf_to_img import pdf_to_image_bytes
from base64 import b64encode
from mysite.s3_file_manager import S3
from django.urls import reverse
from collections import OrderedDict
from mysite.order.models import Order
from .models import TestSheet, Equipment
from mysite.dbmanagement.models import EquipmentManufacturer


@login_required
def order_update(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    dsq = this_order.data_sheets.all()
    _eq_types = Equipment.objects.exclude(test_sheet__isnull=True)
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

    ـequipments = []
    if not dsq.exists():
        estimate = this_order.proposal.quote.estimate.estimateequipment_set.all()
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
        for eq in dsq:
            ـequipments.append({
                'id': eq.id,
                'equipment': eq.equipment_type.name,
                'eq_id': eq.equipment_type.id,
                'service': eq.equipment_type.service.name,
                'test_sheet': eq.equipment_type.test_sheet.name,
                'eq': eq,
                'qty': 1,
                'qty_range': range(1),
                'type': 'datasheetequipment',
                'has_terminal': DataSheet.objects.filter(parent=eq, equipment_type__name='Air Terminal').exists(),
                # 
                'general_url': None,
                'design_url': None,
                'actual_url': None,
                'general_colour': None,
                'design_colour': None,
                'actual_colour': None,
            })
        nested_dict = {}
        for eq in ـequipments:
            service = eq['service']
            equipment_id = eq['id']
            test_sheet = eq['test_sheet']
            if service not in nested_dict:
                nested_dict[service] = {}
            if test_sheet not in nested_dict[service]:
                nested_dict[service][test_sheet] = {}
            # nested_dict[service][test_sheet][equipment_id] = eq['equipment']
            nested_dict[service][test_sheet][equipment_id] = eq
        ـequipments = nested_dict
        if 'Air Terminal' in ـequipments['Air Balancing']:
            del ـequipments['Air Balancing']['Air Terminal']

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

    # _s3 = S3()
    image_data_list = []
    # for _fl in [
    #     # this_order.equipment_submittal, 
    #     this_order.colored_drawing, 
    #     # this_order.report_colored_drawing, 
    #     # this_order.field_draw, 
    #     # this_order.site_pictures,
    #     # this_order.test_sheets
    # ]:
    #     if not _fl:
    #         continue
    #     if _fl.name.endswith('.pdf'):
    #         # _fl_path = _s3.get_bucket_object("media/" + _fl.name)
    #         # DEBUG using local media
    #         _fl_path = "http://itab-test-server.airdec.net:8000/" + settings.MEDIA_URL + "/" + _fl.name
    #         image_bytes_list = pdf_to_image_bytes(_fl_path)
    #         image_data_list = [b64encode(img_bytes).decode('utf-8') for img_bytes in image_bytes_list]
    #     else:
    #         image_data_list.append(_fl_path)

    context = {
        "order": this_order,
        "equipments": ـequipments,
        "eq_types": eq_types,
        "test_sheets": test_sheets,
        "maps": image_data_list,
        "modules_type": modules_type,
        "manufacturers": manufacturers,
    }
    return render(request, "order_edit.html", context)


@login_required
def equipment_update(request, equipment_id):
    ds = get_object_or_404(DataSheet, pk=equipment_id)
    order = get_object_or_404(Order, pk=ds.project.id)
    parents = order.data_sheets.exclude(id=equipment_id)
    _parents = []
    for parent in parents:
        title = parent.code
        if not title:
            title = parent.fan_no
        if not title:
            title = f"{parent.id} - " + parent.name
        _parents.append({
            'id': parent.id,
            'title': title,
        })
    manufacturers = EquipmentManufacturer.objects.all()
    context = {
        "ds": ds,
        "manufacturers": manufacturers,
        "parents": _parents
    }
    return render(request, "equipment_update.html", context)


@login_required
def equipment_forms_update(request, equipment_id):
    t = request.GET.get('t', None)
    ds = get_object_or_404(DataSheet, pk=equipment_id)
    fields = ds.form_fields[t]
    sorted_fields = dict(sorted(fields.items(), key=lambda item: item[1]['order']))
    context = {
        "ds": ds,
        "fields": sorted_fields,
        "t": t,
    }
    return render(request, "equipment_forms_update.html", context)


@login_required
def terminals_update(request, datasheet_id):
    my_sheet = DataSheet.objects.filter(parent=datasheet_id, equipment_type__name='Air Terminal')
    terminal_types = {}
    if len(my_sheet.filter(_type=1)) > 0:
        terminal_types['Supply Terminals'] = my_sheet.filter(_type=1)
    if len(my_sheet.filter(_type=2)) > 0:
        terminal_types['Return Terminals'] = my_sheet.filter(_type=2)
    if len(my_sheet.filter(_type=3)) > 0:
        terminal_types['Outside Terminals'] = my_sheet.filter(_type=3)
    if len(my_sheet.filter(_type=4)) > 0:
        terminal_types['Exhaust Terminals'] = my_sheet.filter(_type=4)

    terminal_fields = {}
    for key, terminals in terminal_types.items():
        terminal_fields[key] = []
        for terminal in terminals:
            t = request.GET.get('t', None)  # This assumes 't' parameter tells which fields to load, may need adjustment based on actual use
            form_fields = terminal.form_fields[t] if terminal and hasattr(terminal, 'form_fields') and t in terminal.form_fields else {}
            form_fields = dict(sorted(form_fields.items(), key=lambda item: item[1]['order']))
            terminal_fields[key].append((terminal, form_fields))

    parameters = {
        'terminal_types': terminal_fields,  # This now includes both terminals and their specific fields
        'ds': my_sheet.first()
    }
    return render(request, "air_terminals_update.html", parameters)

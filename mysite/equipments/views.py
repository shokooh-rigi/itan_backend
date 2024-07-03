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
            })
        nested_dict = {}
        for eq in ـequipments:
            service = eq['service']
            equipment_type = eq['equipment']
            equipment_id = eq['id']
            if service not in nested_dict:
                nested_dict[service] = {}
            if equipment_type not in nested_dict[service]:
                nested_dict[service][equipment_type] = {}
            nested_dict[service][equipment_type][equipment_id] = eq['equipment']
        ـequipments = nested_dict

            # if eq.sheet.test_sheet_type.name.lower() == "air moving":
            #     if not eq.equipment.main_data_entry_confirmed:
            #         equipments_dict[key]['general_url'] = reverse('sheetEquipmentCommonData', args=[eq.id])
            #     else:
            #         equipments_dict[key]['general_url'] = reverse('sheetEquipmentCommonDataEdit', args=[eq.id])
            #     equipments_dict[key]['design_url'] = reverse('sheetEquipmentDesignValue', args=[eq.id])
            #     if not eq.equipment.actual_data_entry_confirmed:
            #         equipments_dict[key]['actual_url'] = reverse('sheetEquipmentActualValue', args=[eq.id])
            #     else:
            #         equipments_dict[key]['actual_url'] = reverse('sheetEquipmentActualValueEdit', args=[eq.id])
            # else:
            #     equipments_dict[key]['general_url'] = reverse('vavSheetEquipmentGeneralData', args=[eq.id])
            #     equipments_dict[key]['design_url'] = reverse('vavSheetEquipmentDesignData', args=[eq.id])
            #     equipments_dict[key]['actual_url'] = reverse('vavSheetEquipmentActualData', args=[eq.id])
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
                # if eq.equipment.main_data_entry_confirmed:
                #     equipments_dict[key]['general_colour'] = '#008000'
                # if eq.equipment.design_data_entry_confirmed:
                #     equipments_dict[key]['design_colour'] = '#008000'
                # if eq.equipment.actual_data_entry_confirmed:
                #     equipments_dict[key]['actual_colour'] = '#008000'


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
    context = {
        "ds": ds,
    }
    return render(request, "equipment_update.html", context)

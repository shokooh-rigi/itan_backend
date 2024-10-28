import math

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .forms import *
from .models import *
from ..sheetcreator.models import *
from django.db.models import Count

from django.conf import settings

from mysite.equipments.models import DataSheet
from mysite.order.models import Order
from django.conf import settings

from mysite.utils.pdf_to_img import pdf_to_image_bytes
from base64 import b64encode
from .utils import *


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
        context['general_info']['guaranty']['address2'] += " " + order.proposal.quote.estimate.project.zip
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
        context['general_info']['guaranty']['eng_firm_address2'] += ", " + order.proposal.quote.estimate.engineer.company.zip
    if not context['general_info']['guaranty']['eng_firm_address']:
        context['general_info']['guaranty']['eng_firm_address'] = "N.S."
    if not context['general_info']['guaranty']['eng_firm_address2']:
        context['general_info']['guaranty']['eng_firm_address2'] = "N.S."

    datasheets = order.data_sheets.all()
    page_counter = 1
    # Air Moving
    air_moving_equipments = datasheets.filter(equipment_type__test_sheet__name__iexact='Air Moving').all().order_by('id')
    if len(air_moving_equipments) > 0:
        for air_moving_equipment in air_moving_equipments:
            air_moving_data = fetch_air_mov_data(air_moving_equipment)
            # Notes (returns list)
            air_moving_data, notes = handle_notes([air_moving_data], "air_moving")
            # clean up fields and use values not notes
            air_moving_data = set_field_value(air_moving_data)
            # Clean up any fields that are empty or None
            air_moving_data = handle_empty_fields(air_moving_data, "air_moving")
            # Convert all values to upper case
            air_moving_data = handle_uppercase_fields(air_moving_data, "air_moving")

            context['pages'].append({
                'type': 'AIRMOVING',
                'system': air_moving_equipment.fan_no,
                'data': air_moving_data,
                'notes': notes,
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
    vav_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='V.A.V').all().order_by('id')
    VAV_IN_ONE_PAGE = 12
    if len(vav_equipments) > 0:
        vavs_data = fetch_vav_data(vav_equipments)
        if len(vavs_data) > 0:
            for i in range(math.ceil(len(vavs_data) / VAV_IN_ONE_PAGE)):
                page_items = vavs_data[i * VAV_IN_ONE_PAGE: (i + 1) * VAV_IN_ONE_PAGE]
                # Notes
                page_items, notes = handle_notes(page_items, "vav")
                # clean up fields and use values not notes
                page_items = set_field_value(page_items)
                # Clean up any fields that are empty or None
                page_items = handle_empty_fields(page_items, "vav")
                # Convert all values to upper case
                page_items = handle_uppercase_fields(page_items, "vav")
                # Add empty rows to fill the page
                if len(page_items) < VAV_IN_ONE_PAGE:
                    empty_slots = VAV_IN_ONE_PAGE - len(page_items)
                    page_items.extend([{}] * empty_slots)

                context['pages'].append({
                    'type': 'VAV',
                    'system': 'VAVs',
                    'data': page_items,
                    'notes': notes,
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
                this_page_vav_ids = [k.get('id', 0) for k in page_items]
                this_page_vav_ids = [k for k in this_page_vav_ids if k]
                # Air Terminal
                this_vav_terminals = datasheets.filter(parent__in=this_page_vav_ids, equipment_type__test_sheet__name__iexact='Air Terminal').all().order_by('_type', 'outlet_no')
                if len(this_vav_terminals) > 0:
                    toc.append({
                        'name': 'AIR TERMINAL TEST SHEET',
                        'page': page_counter,
                        'level': 1,
                        'underline': False
                    })
                for this_vav_ in page_items:
                    if not this_vav_:
                        continue
                    this_vav_terminals = datasheets.filter(parent__id=this_vav_['id'], equipment_type__test_sheet__name__iexact='Air Terminal').all().order_by('_type', 'outlet_no')
                    if len(this_vav_terminals) > 0:
                        for _t in [1, 2, 3, 4]:
                            this_terminals = this_vav_terminals.filter(_type=_t)
                            if this_terminals:
                                terminals_data = fetch_terminal_data(this_terminals, _t)
                                context['pages'].append(terminals_data)
                                page_counter += 1

    # Pump
    pump_equipments = datasheets.filter(equipment_type__test_sheet__name__iexact='Pump').all().order_by('id')
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
    velocity_traverse_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='Velocity Traverse').all().order_by('id')
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
    flow_measuring_equipments = datasheets.filter(equipment_type__test_sheet__name__icontains='Flow Measuring').all().order_by('id')
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
    other_terminal_equipments = datasheets.filter(equipment_type__name__icontains='Other Air Terminal').all().order_by('id')
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
                this_terminals = this_terminals_set.filter(_type=_t)
                if this_terminals:
                    terminals_data = fetch_terminal_data(this_terminals, _t)
                    context['pages'].append(terminals_data)
        # else add 1 empty page for each other terminal
        else:
            terminals_data = fetch_terminal_data([], 5)
            toc.append({
                'name': "Other Air Terminal",
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

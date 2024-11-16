from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import DataSheet
from mysite.utils.pdf_to_img import pdf_to_image_bytes
from base64 import b64encode
from mysite.s3_file_manager import S3
from mysite.order.models import Order
from .models import TestSheet, Equipment
from mysite.dbmanagement.models import EquipmentManufacturer


@login_required
def order_update(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    order_data_sheets = this_order.data_sheets.all()
    db_equipment_types = Equipment.objects.exclude(test_sheet__isnull=True)
    manufacturers = EquipmentManufacturer.objects.all()
    manufacturers = sorted(manufacturers, key=lambda x: x.name)
    modules_type = "Equipments"
    equipment_type_list = []
    for db_equipment_type in db_equipment_types:
        equipment_type_list.append({
            'id': db_equipment_type.id,
            'name': db_equipment_type.name,
            'test_sheet': db_equipment_type.test_sheet.name,
            'test_sheet_id': db_equipment_type.test_sheet.id,
        })
    equipment_type_list = sorted(equipment_type_list, key=lambda x: x['name'])
    _test_sheets = TestSheet.objects.all()
    test_sheets = []
    for ts in _test_sheets:
        test_sheets.append({
            'id': ts.id,
            'name': ts.name,
        })
    test_sheets = sorted(test_sheets, key=lambda x: x['name'])
    # this is the final list of equipments that will be shown in the template
    equipments = []
    # If there are no datasheets for this order (previously not created), we need to show the equipment list from the estimate
    if not order_data_sheets.exists():
        estimate_equipments = this_order.proposal.estimate.estimateequipment_set.all()
        if estimate_equipments.exists():
            modules_type = "Estimate"
            for equipment in estimate_equipments:
                # Based on the project's requirements we may need to exclude RGD equipment from the list
                # This order came from Mrs. Farahvashi
                if equipment.equipment.name == "RGD":
                    continue
                equipments.append({
                    'id': equipment.id,
                    'equipment': equipment.equipment.name,
                    'eq_id': equipment.equipment.id,
                    'test_sheet': equipment.equipment.test_sheet.name if equipment.equipment.test_sheet else None,
                    'test_sheet_id': equipment.equipment.test_sheet.id if equipment.equipment.test_sheet else None,
                    'service': equipment.estimate.service.name,
                    'qty': int(equipment.quantity),
                })
    # if there are datasheets for this order, we need to show the datasheets and their equipment
    else:
        # TODO: equipments are not really equipments here, they are datasheets. we need to separate it into two views and templates
        for equipment in order_data_sheets:
            equipments.append({
                'id': equipment.id,
                'equipment': equipment.equipment_type.name,
                'eq_id': equipment.equipment_type.id,
                'service': equipment.equipment_type.service.name,
                'test_sheet': equipment.equipment_type.test_sheet.name,
                'eq': equipment,
                'qty': 1,
                'qty_range': range(1),
                'type': 'datasheetequipment',
                'has_terminal': DataSheet.objects.filter(parent=equipment, equipment_type__name='Air Terminal').exists(),
                # 
                'general_url': None,
                'design_url': None,
                'actual_url': None,
                'general_colour': None,
                'design_colour': None,
                'actual_colour': None,
            })
        nested_dict = {}
        for equipment in equipments:
            service = equipment['service']
            equipment_id = equipment['id']
            test_sheet = equipment['test_sheet']
            if service not in nested_dict:
                nested_dict[service] = {}
            if test_sheet not in nested_dict[service]:
                nested_dict[service][test_sheet] = {}
            # nested_dict[service][test_sheet][equipment_id] = eq['equipment']
            nested_dict[service][test_sheet][equipment_id] = equipment
        equipments = nested_dict


        # only show other air terminals in the air balancing section in a separate section
        if 'Air Terminal' in equipments['Air Balancing']:
            keys_to_delete = []
            for eq_id, eq in equipments['Air Balancing']['Air Terminal'].items():
                if eq['equipment'] != 'Other Air Terminal':
                    keys_to_delete.append(eq_id)
            for eq_id in keys_to_delete:
                del equipments['Air Balancing']['Air Terminal'][eq_id]
            if len(equipments['Air Balancing']['Air Terminal']) == 0:
                del equipments['Air Balancing']['Air Terminal']

    # TODO: get the code back to S3 when want to migrate to production
    # _s3 = S3()
    image_data_list = []
    if this_order.colored_drawing and this_order.colored_drawing.name.endswith('.pdf'):
        # _fl_path = _s3.get_bucket_object("media/" + _fl.name)
        # DEBUG using local media
        _fl_path = "http://itab-test-server.airdec.net:8000" + settings.MEDIA_URL + this_order.colored_drawing.name
        # url = _fl_path.replace("//", "/")
        image_bytes_list = pdf_to_image_bytes(_fl_path)
        image_data_list = [b64encode(img_bytes).decode('utf-8') for img_bytes in image_bytes_list]

    context = {
        "order": this_order,
        "equipments": equipments,
        "eq_types": equipment_type_list,
        "test_sheets": test_sheets,
        "maps": image_data_list,
        "modules_type": modules_type,
        "manufacturers": manufacturers,
    }
    return render(request, "equipments_list.html", context)


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
    manufacturers = sorted(manufacturers, key=lambda x: x.name)
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
        'ds': my_sheet.first(),
        't': t,
    }
    return render(request, "air_terminals_update.html", parameters)

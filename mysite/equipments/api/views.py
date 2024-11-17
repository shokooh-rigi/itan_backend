import re
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Equipment, TestSheet
from mysite.sheetcreator.models import DataSheet
from .serializers import EquipmentSerializer, DataSheetSerializer
from ast import literal_eval
from django.shortcuts import get_object_or_404
from mysite.order.models import Order
from datetime import datetime
from mysite.dbmanagement.models import EquipmentManufacturer
import copy
from ..utils.calc_formula import calculate_formula, calc_terminal_ak_factor
from collections import defaultdict

from rest_framework.parsers import MultiPartParser, FormParser



@api_view(['POST'])
def create_equipment(request):
    serializer = EquipmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def retrieve_equipment(request, pk):
    try:
        equipment = Equipment.objects.get(pk=pk)
    except Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = EquipmentSerializer(equipment)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
def update_equipment(request, pk):
    try:
        equipment = Equipment.objects.get(pk=pk)
    except Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = EquipmentSerializer(equipment, data=request.data, partial=True)  # 'PATCH' requests use partial=True
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_equipment(request, pk):
    try:
        equipment = Equipment.objects.get(pk=pk)
    except Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found.'}, status=status.HTTP_404_NOT_FOUND)
    equipment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
def create_data_sheet(request):
    for i in request.data["data"]:
        if "RGD" in i["equipment"]:
            continue
        order = get_object_or_404(Order, project_number=i["project"])
        eq = get_object_or_404(Equipment, name=i["equipment"])
        test_sheet = get_object_or_404(TestSheet, name=i["test_sheet"])
        for j in range(int(i["qty"])):
            obj = DataSheet.objects.create(
                sheet_date=datetime.now().date(),
                equipment_type=eq,
                project=order,
                form_fields=copy.deepcopy(test_sheet.form_fields),
            )
            if eq.test_sheet.name == "Air Moving":
                obj.fan_no = eq.name
            # VAV
            else:
                obj.code = eq.name
            obj.save()
        order.state = "In Progress"
        order.save()
    return Response({"data": "data sheet created"})

@api_view(['GET'])
def retrieve_data_sheet(request, pk):
    try:
        data_sheet = DataSheet.objects.get(pk=pk)
    except DataSheet.DoesNotExist:
        return Response({'error': 'Data Sheet not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = DataSheetSerializer(data_sheet)
    return Response(serializer.data)

# Model fields
@api_view(['PUT', 'PATCH'])
def update_data_sheet(request, pk):
    data_sheet = get_object_or_404(DataSheet, pk=pk)
    for key, value in request.data.items():
        if not value:
            continue
        if key == "manufacturer":
            value = get_object_or_404(EquipmentManufacturer, pk=value)
        elif "_air_terminal" in key:
            # compare with previous value
            prev = getattr(data_sheet, key)
            if int(prev) < int(value):
                for i in range(int(value) - int(prev)):
                    # create new datasheet (air terminal)
                    eq = get_object_or_404(Equipment, name="Air Terminal")
                    _type = 1
                    _code = ""
                    if key == "number_of_supply_air_terminal":
                        _type = 1
                    elif key == "number_of_return_air_terminal":
                        _type = 2
                        _code = "RG"
                    elif key == "number_of_outside_air_terminal":
                        _type = 3
                    elif key == "number_of_exhaust_air_terminal":
                        _type = 4
                    form_fields = copy.deepcopy(eq.test_sheet.form_fields)
                    outlet_no = DataSheet.objects.filter(
                        parent=data_sheet, 
                        equipment_type__name='Air Terminal',
                        _type=_type
                    ).count() + 1
                    form_fields["design"]["Code"]["value"] = _code
                    new_ds = DataSheet.objects.create(
                        sheet_date=datetime.now().date(),
                        equipment_type=eq,
                        name=eq.name,
                        project=data_sheet.project,
                        form_fields=form_fields,
                        parent=data_sheet,
                        outlet_no=outlet_no,
                        _type=_type,
                        code=_code,
                    )

        setattr(data_sheet, key, value)

    # Handle file upload or removal
    if 'remove_attach' in request.data and request.data['remove_attach'] == 'on':
        # Remove the existing file
        data_sheet.attach.delete(save=False)
        data_sheet.attach = None
    elif 'attach' in request.FILES:
        # Assign the uploaded file
        data_sheet.attach = request.FILES['attach']

    data_sheet.main_data_entry_completed = True
    data_sheet.save()
    return Response({"data": "data sheet updated"})

# Form fields
@api_view(['PUT', 'PATCH'])
def update_data_sheet_form(request, pk):
    form_type = request.query_params.get("t")
    data_sheet = get_object_or_404(DataSheet, pk=pk)
    is_air_terminal = request.query_params.get("ds")
    errors = []
    
    # clean data
    data_dict = defaultdict(lambda: defaultdict(dict))
    for key, value_list in request.data.items():
        if isinstance(value_list, str):
            value_list = [value_list]
        value = value_list[0]

        if key.endswith('_note'):
            base_key = key[:-5]
            if is_air_terminal == "air-terminal":
                field_name, id = base_key.rsplit('_', 1)
            else:
                field_name = base_key
                id = data_sheet.pk
            data_dict[id][field_name]['note'] = value
        else:
            if is_air_terminal == "air-terminal":
                field_name, id = key.rsplit('_', 1)
            else:
                field_name = key
                id = data_sheet.pk
            data_dict[id][field_name]['value'] = value
    data_dict = {id: dict(fields) for id, fields in data_dict.items()}

    for ds_id in data_dict:
        data_sheet = get_object_or_404(DataSheet, pk=ds_id)
        org_form_fields = copy.deepcopy(data_sheet.form_fields)
        # update state
        if is_air_terminal == "air-terminal":
            parent = data_sheet.parent
            if form_type == "design":
                parent.terminal_design_data_entry_completed = True
            elif form_type == "actual":
                parent.terminal_actual_data_entry_completed = True
            parent.save()
        else:
            if form_type == "design":
                data_sheet.design_data_entry_completed = True
            elif form_type == "actual":
                data_sheet.actual_data_entry_completed = True
            data_sheet.save()
        new_data = data_dict[ds_id]

        # calc ak factor and fpms
        if is_air_terminal == "air-terminal":
            if form_type == "design":
                _code = new_data["Code"]["value"] if "Code" in new_data else org_form_fields["design"]["Code"]["value"]
                if _code in ["SR", "SG", "OED", "RG", "DUCT"]:
                    new_data["AK Factor"]["value"] = calc_terminal_ak_factor(new_data["Size"]["value"])
                new_data["FPM"]["value"] = calculate_formula(org_form_fields[form_type]["FPM"]["formula"], org_form_fields, new_data, new_data["FPM"], "FPM", form_type)
            elif form_type == "actual":
                new_data["Initial FPM"]["value"] = calculate_formula(org_form_fields[form_type]["Initial FPM"]["formula"], org_form_fields, new_data, new_data["Initial FPM"], "Initial FPM", form_type)
                new_data["Final FPM"]["value"] = calculate_formula(org_form_fields[form_type]["Final FPM"]["formula"], org_form_fields, new_data, new_data["Final FPM"], "Final FPM", form_type)

        # for air moving
        if data_sheet.equipment_type.test_sheet.name == "Air Moving":
            if form_type == "actual":
                # calculate Total SP (Ext. SP)
                total_sp_actual = calculate_formula(org_form_fields[form_type]["Total SP (Ext. SP)"]["formula"], org_form_fields, new_data, new_data["Total SP (Ext. SP)"], "Total SP (Ext. SP)", form_type)
                if total_sp_actual:
                    new_data["Total SP (Ext. SP)"]["value"] = total_sp_actual
                else:
                    # check with regex if either 'Fan (Unit) Suction Pressure' or 'Discharge Pressure, Fan / Unit' has a number in it set it to total sp
                    number_pattern = re.compile(r'\d+')
                    fan_suction_pressure = new_data["Fan (Unit) Suction Pressure"]["value"]
                    discharge_pressure = new_data["Discharge Pressure, Fan / Unit"]["value"]
                    if number_pattern.search(fan_suction_pressure) or number_pattern.search(discharge_pressure):
                        new_data["Total SP (Ext. SP)"]["value"] = fan_suction_pressure if number_pattern.search(fan_suction_pressure) else discharge_pressure
               
        for field_name in org_form_fields[form_type]:
            org_form_fields[form_type][field_name]['note'] = new_data.get(field_name, {}).get('note', '')
            org_form_fields[form_type][field_name]['value'] = new_data.get(field_name, {}).get('value', '')
            computed_value = None
            # calculate formula
            if org_form_fields[form_type][field_name].get('formula', None) and (is_air_terminal != "air-terminal"):
                # since we already calculated Total SP (Ext. SP) above, skip it
                if (field_name == "Total SP (Ext. SP)") and (form_type == "actual") and (data_sheet.equipment_type.test_sheet.name == "Air Moving"):
                    continue
                computed_value = calculate_formula(org_form_fields[form_type][field_name]['formula'], org_form_fields, new_data, org_form_fields[form_type][field_name], field_name, form_type)
                # set formula calculated value
                if (field_name == "Return Air C.F.M."):
                    org_form_fields[form_type][field_name]['formula_calculated'] = computed_value
                else:
                    org_form_fields[form_type][field_name]['value'] = computed_value.strip() if computed_value else computed_value

            # Handle belt drive and direct drive
            if data_sheet.equipment_type.test_sheet.name == "Air Moving":
                if (form_type == "design") and (field_name == "Direct Drive"):
                    if "value" in new_data["Direct Drive"]:
                        if new_data["Direct Drive"]["value"] == "on":
                            org_form_fields["actual"]["Motor Pully"]["value"] = org_form_fields["actual"]["Motor Pully"]["value"] if org_form_fields["actual"]["Motor Pully"]["value"] else "N.A."
                            org_form_fields["actual"]["Fan Pully"]["value"] = org_form_fields["actual"]["Fan Pully"]["value"] if org_form_fields["actual"]["Fan Pully"]["value"] else "N.A."
                            org_form_fields["actual"]["C to C"]["value"] = org_form_fields["actual"]["C to C"]["value"] if org_form_fields["actual"]["C to C"]["value"] else "N.A."
                            org_form_fields["actual"]["Motor Shaft"]["value"] = org_form_fields["actual"]["Motor Shaft"]["value"] if org_form_fields["actual"]["Motor Shaft"]["value"] else "N.A."
                            org_form_fields["actual"]["Fan Shaft"]["value"] = org_form_fields["actual"]["Fan Shaft"]["value"] if org_form_fields["actual"]["Fan Shaft"]["value"] else "N.A."

        # set ak factor and FPMS to * if emoty
        if is_air_terminal == "air-terminal":
            if form_type == "design":
                if not org_form_fields[form_type]["AK Factor"]["value"]:
                    org_form_fields[form_type]["AK Factor"]["value"] = "*"
                if not org_form_fields[form_type]["FPM"]["value"]:
                    org_form_fields[form_type]["FPM"]["value"] = "*"
            elif form_type == "actual":
                if not org_form_fields[form_type]["Initial FPM"]["value"]:
                    org_form_fields[form_type]["Initial FPM"]["value"] = "*"
                if not org_form_fields[form_type]["Final FPM"]["value"]:
                    org_form_fields[form_type]["Final FPM"]["value"] = "*"

        data_sheet.form_fields = org_form_fields
        data_sheet.save()

    if errors:
        return Response({"errors": errors}, status=400)
    return Response({"data": "Data sheet updated successfully"})


@api_view(['DELETE'])
def delete_data_sheet(request, pk):
    try:
        data_sheet = DataSheet.objects.get(pk=pk)
    except DataSheet.DoesNotExist:
        return Response({'error': 'Data Sheet not found.'}, status=status.HTTP_404_NOT_FOUND)
    data_sheet.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
def clear_data_sheet(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.data_sheets.all().delete()
    order.state = "Not Started"
    order.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

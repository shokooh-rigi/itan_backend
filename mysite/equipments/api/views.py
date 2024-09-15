from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Equipment, DataSheet, TestSheet
from .serializers import EquipmentSerializer, DataSheetSerializer
from ast import literal_eval
from django.shortcuts import get_object_or_404
from mysite.order.models import Order
from datetime import datetime
from mysite.dbmanagement.models import EquipmentManufacturer
import copy
from ..utils.calc_formula import calculate_formula

from mysite.generatereport.views import report_sheet_recreate_call
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
    form_fields = copy.deepcopy(data_sheet.form_fields)

    print("===" * 20)
    print(request.data)

    errors = []
    exclude_applied_formula = ["AK Factor"]

    is_air_terminal = request.query_params.get("ds")
    if is_air_terminal == "air-terminal":
        if form_type == "design":
            data_sheet.terminal_design_data_entry_completed = True
        elif form_type == "actual":
            data_sheet.terminal_actual_data_entry_completed = True
        data_sheet.save()
    
        for key, value in request.data.items():
            field_key = key.replace("_note", "")
            data_sheet = get_object_or_404(DataSheet, pk=field_key.split("_")[-1])
            field_key = field_key.split("_")[0]
            form_fields = copy.deepcopy(data_sheet.form_fields)
            if field_key in form_fields[form_type]:
                field_data = form_fields[form_type][field_key]
                # Update field note or value
                if "_note" in key:
                    field_data["note"] = value
                else:
                    field_data["value"] = value
                    # Check and apply formula
                    formula = field_data.get("formula")
                    if formula and field_key not in exclude_applied_formula:
                        computed_value = calculate_formula(formula, form_fields, request.data)
                        # if computed_value is not None and field_data.get("type") == "number":
                        if computed_value is not None:
                            # if value:
                            #     if float(computed_value) != float(value):
                            #         # errors.append(f"Value mismatch for {field_key}: expected {computed_value}, got {value}")
                            #         field_data["value"] = computed_value
                            # else:
                            #     field_data["value"] = computed_value
                            if ('Total SP' in field_key) and ('*' not in computed_value):
                                computed_value = f"{float(computed_value):.2f}"
                            field_data["value"] = computed_value
            data_sheet.form_fields = form_fields
            data_sheet.save()
    else:
        for key, value in request.data.items():
            field_key = key.replace("_note", "")
            
            if field_key in form_fields[form_type]:
                field_data = form_fields[form_type][field_key]
                # Update field note or value
                if "_note" in key:
                    field_data["note"] = value
                else:

                    print("---" * 10)
                    print(field_data)
                    print(field_key, value)

                    field_data["value"] = value
                    if value == "@":
                        field_data["note"] = "See general note"
                    # Check and apply formula
                    formula = field_data.get("formula")
                    if formula and field_key not in exclude_applied_formula:
                        computed_value = calculate_formula(formula, form_fields, request.data)
                        # if computed_value is not None and field_data.get("type") == "number":
                        if computed_value is not None:
                            # if value:
                            #     if "(" in value:
                            #         value = value.split("(")[1].split(")")[0]
                            #     if float(computed_value) != float(value):
                            #         # errors.append(f"Value mismatch for {field_key}: expected {computed_value}, got {value}")
                            #         field_data["value"] = computed_value
                            # else:
                            #     field_data["value"] = computed_value
                            if ('Total SP' in field_key) and ('*' not in computed_value):
                                computed_value = f"{float(computed_value):.2f}"
                            field_data["value"] = computed_value
        data_sheet.form_fields = form_fields

        if form_type == "design":
            data_sheet.design_data_entry_completed = True
        elif form_type == "actual":
            data_sheet.actual_data_entry_completed = True
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


@api_view(['POST'])
def create_report(request, order_id):
    report_type = request.data.get('report_type')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    report_date = request.data.get('report_date')
    revised_date = request.data.get('revised_date')

    # Pass these parameters to your report generation logic
    report = report_sheet_recreate_call(
        request=request,
        order_id=order_id,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        report_date=report_date,
        revised_date=revised_date,
    )
    return Response({"report": report})

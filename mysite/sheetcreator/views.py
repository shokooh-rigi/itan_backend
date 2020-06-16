from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from ..order.models import *
from .forms import *
from ..settings import MEDIA_URL, WEB_URL
from .models import *


# Create your views here.


@login_required
def sheet_list(request):
    project_name = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Sheet.objects.all()

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "sheetList.html", parameters)


@login_required
def sheet_add(request):
    form = SheetForm(request.POST or None, request.FILES or None, initial={'test_sheet_type': 1})
    orders = Order.objects.all()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['test_sheet_type'] = 1
                sheet = form.save()
                return redirect('sheetEquipment', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "sheetAdd.html", parameters)


@login_required
def sheet_equipment(request, sheet_id):
    sheet = Sheet.objects.get(id=sheet_id)
    form = SheetEquipmentForm(request.POST or None, initial={'sheet': sheet_id})

    equipments = Equipment.objects.filter(test_sheet__name__icontains='air mov')

    equipment_in = []
    sheet_equipments = SheetEquipment.objects.filter(sheet=sheet_id)
    for one_sheet_equipment in sheet_equipments:
        equipment_in.append(one_sheet_equipment.equipment_type.id)

    equipments_count = {}
    for one_sheet_equipment in sheet_equipments:
        if one_sheet_equipment.equipment_type.name in equipments_count:
            old_quantity = equipments_count[one_sheet_equipment.equipment_type.name]
            new_quantity = old_quantity + 1
            equipments_count[one_sheet_equipment.equipment_type.name] = new_quantity
        else:
            equipments_count[one_sheet_equipment.equipment_type.name] = 1
    if request.method == 'POST':
        if form.is_valid():
            if SheetEquipment.objects.filter(sheet=sheet_id, equipment_type=form.cleaned_data['equipment_type']).count() == 0:
                form.cleaned_data['sheet'] = sheet_id
                for i in range(0, form.cleaned_data['quantity']):
                    item_sheet_equipment = SheetEquipment()
                    item_sheet_equipment.sheet = Sheet.objects.get(id=sheet_id)
                    item_sheet_equipment.equipment_type = Equipment.objects.get(id=form.cleaned_data['equipment_type'].id)
                    item_sheet_equipment.save()
                return redirect('sheetEquipment', sheet_id)
            else:
                SheetEquipment.objects.filter(sheet=sheet_id, equipment_type=form.cleaned_data['equipment_type']).delete()
                for i in range(0, form.cleaned_data['quantity']):
                    item_sheet_equipment = SheetEquipment()
                    item_sheet_equipment.sheet = Sheet.objects.get(id=sheet_id)
                    item_sheet_equipment.equipment_type = Equipment.objects.get(id=form.cleaned_data['equipment_type'].id)
                    item_sheet_equipment.save()
                return redirect('sheetEquipment', sheet_id)
    first_equipment = sheet_equipments.first()
    if first_equipment is None:
        first_equipment_id = ''
    else:
        first_equipment_id = first_equipment.id
    parameters = {'sheet': sheet,
                  'form': form,
                  'sheet_equipments': sheet_equipments,
                  'equipment_in': equipment_in,
                  'equipments_count': equipments_count,
                  'equipments': equipments,
                  'first_equipment_id': first_equipment_id,
                  }
    return render(request, "sheetEquipment.html", parameters)


@login_required
def equipments_list(request, sheet_id):

    sheet_equipments = SheetEquipment.objects.filter(sheet=sheet_id)

    parameters = {'sheet_equipments': sheet_equipments,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "sheetEquipmentsList.html", parameters)


@login_required
def sheet_equipment_common_data(request, sheet_equipment_id):
    sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    showing_fields = TestSheetColumn.objects.filter(test_sheet__name__icontains='air mov')
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=sheet_equipment.equipment_type)
    Equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__icontains='air mov', equipment_type=sheet_equipment.equipment_type)

    equipments = Equipment.objects.filter(test_sheet__name__icontains='air mov')

    if request.method == 'POST':
        for every_field in showing_fields:
            key = every_field
            field_value = request.POST.get('showing_field_value_'+str(every_field.id))
            new_record = SheetEquipmentCommonData(sheet_equipment_id=sheet_equipment_id, key=key, value=field_value)
            new_record.save()
        new_update = SheetEquipment.objects.get(id=sheet_equipment_id)
        new_update.equipment = EquipmentDb.objects.get(id=request.POST.get('id_equipment'))
        new_update.main_data_entry_completed = True
        new_update.save()
        return redirect('sheetEquipmentDesignValue', new_update.id)


    parameters = {'sheet_equipment': sheet_equipment,
                  'showing_fields': showing_fields,
                  'manufacturers': manufacturers,
                  'Equipment_db': Equipment_db,
                  }

    return render(request, "sheetEquipmentCommonData.html", parameters)


@login_required
def review_equipment_values(request, sheet_equipment_id):
    this_sheet_equipment = get_object_or_404(SheetEquipment, id=sheet_equipment_id)
    this_equipment = this_sheet_equipment.equipment
    custom_fields = this_equipment.equipment_type.equipmenttypecustomfield_set.all()
    custom_operations = this_equipment.equipment_type.equipmenttypecustomoperation_set.all()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            for custom_field in custom_fields:
                if custom_field.field_range_or_selective == 1:
                    if custom_field.field_type == 3:
                        break
                    my_range = custom_field.field_range.split('-')
                    min_value = my_range[0]
                    max_value = my_range[1]
                    sent_value = request.POST.get('company_value_' + str(custom_field.id))
                    if custom_field.field_type == 1:
                        sent_value = int(sent_value)
                        min_value = int(min_value)
                        max_value = int(max_value)
                    elif custom_field.field_type == 2:
                        sent_value = float(sent_value)
                        min_value = float(min_value)
                        max_value = float(max_value)
                    if sent_value < min_value or sent_value > max_value:
                        error_msg = custom_field.field_name + " Value is not in Range!"
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_field.field_range_or_selective == 2:
                    if custom_field.field_type == 3:
                        break
                    my_range = custom_field.field_range.split(',')
                    sent_value = request.POST.get('company_value_' + str(custom_field.id))
                    is_in_my_range = 0
                    for number in my_range:
                        if custom_field.field_type == 1:
                            if int(number) == int(sent_value):
                                is_in_my_range = 1
                        elif custom_field.field_type == 2:
                            if float(number) == float(sent_value):
                                is_in_my_range = 1
                    if is_in_my_range == 0:
                        error_msg = custom_field.field_name + " Value is not selected right!"
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
            for custom_operation in custom_operations:
                this_operation = str(custom_operation.operation)
                this_result = str(custom_operation.result_field)
                operation_msg = str(custom_operation.operation)
                result_msg = str(custom_operation.result_field)
                for custom_field in custom_fields:
                    this_operation = this_operation.replace('[field-' + str(custom_field.id) + ']',
                                                            request.POST.get('company_value_' + str(custom_field.id)))
                    this_result = this_result.replace('[field-' + str(custom_field.id) + ']',
                                                      request.POST.get('company_value_' + str(custom_field.id)))
                    operation_msg = operation_msg.replace('[field-' + str(custom_field.id) + ']', custom_field.field_name)
                    result_msg = result_msg.replace('[field-' + str(custom_field.id) + ']', custom_field.field_name)
                if custom_operation.operand_type == 1:
                    if eval(this_operation) != eval(this_result):
                        error_msg = operation_msg + " must be equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == 2:
                    if eval(this_operation) <= eval(this_result):
                        error_msg = operation_msg + " must be greater than " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == 3:
                    if eval(this_operation) < eval(this_result):
                        error_msg = operation_msg + " must be greater than or equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == 4:
                    if eval(this_operation) >= eval(this_result):
                        error_msg = operation_msg + " must be smaller than " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == 5:
                    if eval(this_operation) > eval(this_result):
                        error_msg = operation_msg + " must be smaller than or equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)

            for custom_field in custom_fields:
                num_results = EquipmentCustomField.objects.filter(equipment_value_name=custom_field.field_name,
                                                                  equipment=this_equipment.id).count()
                if num_results > 0:
                    EquipmentCustomField.objects.filter(equipment_value_name=custom_field.field_name,
                                                        equipment=this_equipment.id).update(company_value=request.POST.get('company_value_' + str(custom_field.id)))
                else:
                    new_object = EquipmentCustomField(equipment_value_name=custom_field.field_name, company_value=request.POST.get('company_value_' + str(custom_field.id)), equipment=this_equipment)
                    new_object.save()
            return redirect('sheetEquipmentActualValue', sheet_equipment_id)
    parameters = {'this_equipment': this_equipment,
                  'custom_fields': custom_fields,
                  }
    return render(request, "EquipmentDesignValue.html", parameters)


@login_required
def equipment_actual_values(request, sheet_equipment_id):
    this_sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    custom_fields = EquipmentCustomField.objects.filter(equipment=this_sheet_equipment.equipment)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            for custom_field in custom_fields:
                num_results = SheetEquipmentActualData.objects.filter(key__equipment_value_name=custom_field.equipment_value_name,
                                                                  sheet_equipment=this_sheet_equipment.id).count()
                if num_results > 0:
                    SheetEquipmentActualData.objects.filter(key__equipment_value_name=custom_field.equipment_value_name,
                                                                  sheet_equipment=this_sheet_equipment).update(value=request.POST.get('actual_value_' + str(custom_field.id)))
                else:
                    new_object_key = EquipmentCustomField.objects.get(equipment=this_sheet_equipment.equipment, equipment_value_name=custom_field.equipment_value_name)
                    new_object = SheetEquipmentActualData(key=new_object_key, value=request.POST.get('actual_value_' + str(custom_field.id)), sheet_equipment=this_sheet_equipment)
                    new_object.save()
            this_sheet_equipment.actual_data_entry_completed = True
            this_sheet_equipment.save()
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
    parameters = {'this_sheet_equipment': this_sheet_equipment,
                  'custom_fields': custom_fields,
                  }
    return render(request, "EquipmentActualValue.html", parameters)


@login_required
def equipment_actual_values_edit(request, sheet_equipment_id):
    this_sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    custom_fields = SheetEquipmentActualData.objects.filter(sheet_equipment=this_sheet_equipment)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            for custom_field in custom_fields:
                SheetEquipmentActualData.objects.filter(key=custom_field.key,
                                                        sheet_equipment=this_sheet_equipment).update(value=request.POST.get('actual_value_' + str(custom_field.id)))
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
    parameters = {'this_sheet_equipment': this_sheet_equipment,
                  'custom_fields': custom_fields,
                  }
    return render(request, "EquipmentActualValueEdit.html", parameters)


@login_required
def sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(Sheet, id=sheet_id)
    if request.POST.get("confirm"):
        this_sheet.delete()
        return redirect('sheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "sheet_delete.html", parameters)


@login_required
def sheet_equipment_delete(request, sheet_id, sheet_equipment_name):
    this_sheet = SheetEquipment.objects.filter(equipment_type__name__iexact=sheet_equipment_name, sheet=sheet_id)
    if request.POST.get("confirm"):
        this_sheet.delete()
        return redirect('sheetEquipment', sheet_id)
    parameters = {'this_sheet': this_sheet,
                  'sheet_equipment_name': sheet_equipment_name,
                  }
    return render(request, "sheet_delete.html", parameters)

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from mysite.dbmanagement.models import EquipmentCustomField
from .forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse


@login_required
def equipment_db(request):
    project_name = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = EquipmentDb.objects.filter(Q(model_number__icontains=project_name) |
                                             Q(equipment_type__name__icontains=project_name)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    equipments = paginator.get_page(page)

    parameters = {'equipments': equipments,
                  }
    return render(request, "equipments_db.html", parameters)


@login_required
def equipment_create(request):
    form = EquipmentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('EquipmentsHome')
        if form.is_valid():
            if request.POST.get("save"):
                this_equipment = form.save()
                return redirect('EquipmentsValues', this_equipment.pk)
    parameters = {'form': form,
                  'page_title': 'Create',
                  'page_button': 'Create',
                  }
    return render(request, "equipment_create.html", parameters)


@login_required
def equipment_edit(request, equipment_id):
    this_equipment = get_object_or_404(EquipmentDb, id=equipment_id)
    form = EquipmentForm(request.POST or None, request.FILES or None, instance=this_equipment)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('EquipmentsHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('EquipmentsHome')
    parameters = {'form': form,
                  'this_equipment': this_equipment,
                  'page_title': 'Edit',
                  'page_button': 'Save',
                  }
    return render(request, "equipment_create.html", parameters)


@login_required
def equipment_values(request, equipment_id):
    this_equipment = get_object_or_404(EquipmentDb, id=equipment_id)
    custom_fields = this_equipment.equipment_type.equipmenttypecustomfield_set.all()
    custom_operations = this_equipment.equipment_type.equipmenttypecustomoperation_set.all()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('EquipmentsHome')
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
                        return render(request, "equipment_fields.html", parameters)
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
                        return render(request, "equipment_fields.html", parameters)
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
                        return render(request, "equipment_fields.html", parameters)
                elif custom_operation.operand_type == 2:
                    if eval(this_operation) <= eval(this_result):
                        error_msg = operation_msg + " must be greater than " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "equipment_fields.html", parameters)
                elif custom_operation.operand_type == 3:
                    if eval(this_operation) < eval(this_result):
                        error_msg = operation_msg + " must be greater than or equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "equipment_fields.html", parameters)
                elif custom_operation.operand_type == 4:
                    if eval(this_operation) >= eval(this_result):
                        error_msg = operation_msg + " must be smaller than " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "equipment_fields.html", parameters)
                elif custom_operation.operand_type == 5:
                    if eval(this_operation) > eval(this_result):
                        error_msg = operation_msg + " must be smaller than or equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'custom_fields': custom_fields,
                                      'error_msg': error_msg,
                                      }
                        return render(request, "equipment_fields.html", parameters)

            for custom_field in custom_fields:
                num_results = EquipmentCustomField.objects.filter(equipment_value_name=custom_field.field_name,
                                                                  equipment=this_equipment.id).count()
                if num_results > 0:
                    EquipmentCustomField.objects.filter(equipment_value_name=custom_field.field_name,
                                                        equipment=this_equipment.id).update(company_value=request.POST.get('company_value_' + str(custom_field.id)))
                else:
                    new_object = EquipmentCustomField(equipment_value_name=custom_field.field_name, company_value=request.POST.get('company_value_' + str(custom_field.id)), equipment=this_equipment)
                    new_object.save()
            return redirect('EquipmentsHome')
    parameters = {'this_equipment': this_equipment,
                  'custom_fields': custom_fields,
                  }
    return render(request, "equipment_fields.html", parameters)


@login_required
def equipment_delete(request, equipment_id):
    this_equipment = get_object_or_404(EquipmentDb, id=equipment_id)
    if request.POST.get("confirm"):
        this_equipment.delete()
        this_equipment.equipmentcustomfield_set.all().delete()
        return redirect('EquipmentsHome')
    parameters = {'this_equipment': this_equipment,
                  }
    return render(request, "equipment_delete.html", parameters)


@login_required
def manufacturer_create_popup(request):
    form = ManufacturerForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer");</script>' % (instance.pk, instance))

    return render(request, "manufacturer_form.html", {"form": form})


@login_required
def manufacturer_edit_popup(request, pk=None):
    instance = get_object_or_404(EquipmentManufacturer, pk=pk)
    form = ManufacturerForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer");</script>' % (instance.pk, instance))

    return render(request, "manufacturer_form.html", {"form": form})

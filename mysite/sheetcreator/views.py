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
                for every_quantity in form.cleaned_data['quantity']:
                    form.save()
                return redirect('sheetEquipment', sheet_id)
    first_equipment = sheet_equipments.first()
    parameters = {'sheet': sheet,
                  'form': form,
                  'sheet_equipments': sheet_equipments,
                  'equipment_in': equipment_in,
                  'equipments_count': equipments_count,
                  'equipments': equipments,
                  }
    return render(request, "sheetEquipment.html", parameters)


@login_required
def sheet_equipment_common_data(request, sheet_equipment_id):
    sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    showing_fields = TestSheetColumn.objects.filter(test_sheet__name__icontains='air mov')
    manufacturers = EquipmentManufacturer.objects.all()
    Equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__icontains='air mov')

    equipments = Equipment.objects.filter(test_sheet__name__icontains='air mov')

    if request.method == 'POST':
        for every_field in showing_fields:
            key = every_field
            field_value = request.POST.get('showing_field_value_'+str(every_field.id))
            new_record = SheetEquipmentCommonData(sheet_equipment_id=sheet_equipment_id, key=key, value=field_value)
            new_record.save()
        new_update = SheetEquipment.objects.get(id=sheet_equipment_id)
        new_update.equipment = EquipmentDb.objects.get(id=request.POST.get('id_equipment'))
        new_update.save()

    parameters = {'sheet_equipment': sheet_equipment,
                  'showing_fields': showing_fields,
                  'manufacturers': manufacturers,
                  'Equipment_db': Equipment_db,
                  }

    return render(request, "sheetEquipmentCommonData.html", parameters)

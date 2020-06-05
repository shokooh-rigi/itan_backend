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
        equipment_in.append(one_sheet_equipment.equipment.id)
    if request.method == 'POST':
        if form.is_valid():
            if SheetEquipment.objects.filter(sheet=sheet_id, equipment=form.cleaned_data['equipment']).count() == 0:
                form.cleaned_data['sheet'] = sheet_id
                form.save()
                return redirect('sheetEquipment', sheet_id)
            else:
                SheetEquipment.objects.filter(sheet=sheet_id, equipment=form.cleaned_data['equipment']) \
                    .update(quantity=form.cleaned_data['quantity'])
                return redirect('sheetEquipment', sheet_id)
    parameters = {'sheet': sheet,
                  'form': form,
                  'sheet_equipments': sheet_equipments,
                  'equipment_in': equipment_in,
                  'equipments': equipments,
                  }
    return render(request, "sheetEquipment.html", parameters)


@login_required
def order_edit(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    proposals = Proposal.objects.filter(archive=False).exclude(id__in=Order.objects.all().values_list('proposal_id'))
    change_orders = ChangeOrder.objects.filter(order=order_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderHome')
        if request.POST.get("co"):
            return redirect('changeOrder', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('orderHome')
    parameters = {'form': form,
                  'proposals': proposals,
                  'change_orders': change_orders,
                  'order_id': order_id,
                  'this_order': this_order,
                  }
    return render(request, "orderEdit.html", parameters)


@login_required
def order_delete(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    if request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_order.delete()
        return redirect('orderHome')
    elif request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_order': this_order,
                'error_msg': error_msg
            }
            return render(request, "orderDelete.html", parameters)
        return redirect('orderHome')
    parameters = {'this_order': this_order
                  }
    return render(request, "orderDelete.html", parameters)


@login_required
def order_archive(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    if request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_order.archive = True
            this_order.save()
        return redirect('orderHome')
    elif request.method == "POST" and request.user.is_authenticated and this_order.proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_order': this_order,
                'error_msg': error_msg
            }
            return render(request, "orderArchive.html", parameters)
        return redirect('orderHome')
    parameters = {'this_order': this_order
                  }
    return render(request, "orderArchive.html", parameters)


@login_required
def change_order(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = ChangeOrderForm(request.POST or None, request.FILES or None, initial={'order': order_id})
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['order'] = order_id
                form.save()
                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  }
    return render(request, "changeOrder.html", parameters)


@login_required
def change_order_delete(request, order_id, change_order_id):
    this_change_order = get_object_or_404(ChangeOrder, id=change_order_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_change_order.delete()
        return redirect('orderEdit', order_id=order_id)
    parameters = {'this_change_order': this_change_order
                  }
    return render(request, "changeOrderDelete.html", parameters)

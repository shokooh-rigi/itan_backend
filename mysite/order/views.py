from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django import forms
from platform import system
import os
from .forms import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL


# Create your views here.


@login_required
def order_list(request):
    project_name = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Order.objects.filter(Q(proposal__quote__estimate__project__name__icontains=project_name) |
                                       Q(project_number__icontains=project_name)).order_by(ordering)

    if request.GET.get('type') == 'all' or request.GET.get('type') is None:
        object_list = object_list
    if request.GET.get('type') == 'inprogress':
        object_list = object_list.filter(invoice__isnull=True).filter(report__isnull=True)
    if request.GET.get('type') == 'invoiced':
        object_list = object_list.filter(invoice__isnull=False)
    if request.GET.get('type') == 'reported':
        object_list = object_list.filter(report__isnull=False)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    parameters = {'orders': orders,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "order.html", parameters)


@login_required
def order_add(request, proposal_id=None):
    form = OrderForm(request.POST or None, request.FILES or None)
    if proposal_id:
        proposals = Proposal.objects.filter(id=proposal_id)
    else:
        proposals = Proposal.objects.filter(archive=False).exclude(id__in=Order.objects.all().values_list('proposal_id')).order_by('-created_on')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.save()
                return redirect('orderHome')
    parameters = {'form': form,
                  'proposals': proposals
                  }
    return render(request, "orderAdd.html", parameters)


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
        if request.POST.get("cs"):
            return redirect('controlSystem', order_id=order_id)
        if request.POST.get("es"):
            return redirect('equipmentSubmittal', order_id=order_id)
        if request.POST.get("tl"):
            return redirect('techLabel', order_id=order_id)
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


def tech_label(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    this_techlabel = TechLabel.objects.filter(order__id=order_id).first()
    if this_techlabel:
        form = TechLabelForm(request.POST or None, instance=this_techlabel)
    else:
        form = TechLabelForm(request.POST or None, initial={'order': order_id})
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['order'] = order_id
                form.save()
                return redirect('orderEdit', order_id=order_id)
            if request.POST.get("savep"):
                form.cleaned_data['order'] = order_id
                this_tech_label = form.save()
                parameters = {'form': form,
                              'datenow': datetime.datetime.now().date(),
                              'file_name': 'techlabel-' + str(this_order.project_number),
                              'tech_label': this_tech_label,
                              'license_owner': LicenseInfo.objects.get(key='OwnerName').value,
                              'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
                              'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
                              'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                              'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                              'company_name': LicenseInfo.objects.get(key='CompanyName').value,
                              'WEB_URL': WEB_URL,
                              'STATIC_URL': STATIC_URL,
                              'MEDIA_URL': MEDIA_URL,
                              'os': system(),
                              }
                techlabel_pdf = TechLabel.create_techlabel_pdf(parameters)
                parameters['techlabel_pdf'] = techlabel_pdf[1]
                file_path = os.path.join(settings.MEDIA_ROOT, parameters['techlabel_pdf'])
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type="application/pdf")
                        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                        return response
                raise Http404
    parameters = {'form': form,
                  'this_order': this_order,
                  }
    return render(request, "techLabel.html", parameters)


@login_required
def control_system(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['proposal'] = this_order.proposal
                form.cleaned_data['po_number'] = this_order.po_number
                form.save()
                return redirect('controlSystem', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  }
    return render(request, "controlSystem.html", parameters)


@login_required
def order_equipment_submittal(request, order_id):
    this_order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, request.FILES or None, instance=this_order)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('orderEdit', order_id=order_id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['proposal'] = this_order.proposal
                form.cleaned_data['po_number'] = this_order.po_number
                form.save()
                return redirect('orderEdit', order_id=order_id)
    parameters = {'form': form,
                  'this_order': this_order,
                  }
    return render(request, "EquipmentSubmittal.html", parameters)


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


@login_required
def cs_create_popup(request):
    form = ControlSystemForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_cs");</script>' % (instance.pk, instance))

    return render(request, "cs_form.html", {"form": form})


@login_required
def cs_edit_popup(request, pk=None):
    instance = get_object_or_404(ControlSystem, pk=pk)
    form = ControlSystemForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_control_system");</script>' % (instance.pk, instance))

    return render(request, "cs_form.html", {"form": form})


@login_required
def cs_manufacturer_create_popup(request):
    form = ControlSystemManufacturerForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer");</script>' % (instance.pk, instance))

    return render(request, "cs_manufacturer_form.html", {"form": form})


@login_required
def manufacturer_edit_popup(request, pk=None):
    instance = get_object_or_404(ControlSystemManufacturer, pk=pk)
    form = ControlSystemManufacturerForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(
            '<script>opener.closePopup(window, "%s", "%s", "#id_manufacturer");</script>' % (instance.pk, instance))

    return render(request, "cs_manufacturer_form.html", {"form": form})

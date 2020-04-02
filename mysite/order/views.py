from django.shortcuts import render, redirect, get_object_or_404, reverse
from .forms import *
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.generic import ListView
from datetime import datetime
from ..settings import MEDIA_URL, MEDIA_URL_NOSLASH, WEB_URL, STATIC_URL
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

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

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    parameters = {'orders': orders,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "order.html", parameters)


@login_required
def order_add(request):
    form = OrderForm(request.POST or None, request.FILES or None)
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
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('orderHome')
    parameters = {'form': form,
                  'proposals': proposals,
                  'change_orders': change_orders,
                  'order_id': order_id,
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

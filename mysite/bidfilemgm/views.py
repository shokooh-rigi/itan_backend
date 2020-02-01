from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import datetime
from .forms import BidFileForm
from .models import BidFile
from django.db.models import Q
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from django import forms
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import FormView
from zipfile import ZipFile

# Create your views here.


@login_required
def bid_files_list(request):
    search = request.GET.get('search', '')
    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')
    ordering = 'due_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    from_date = request.GET.get("fromDate", '01/01/2000')
    to_date = request.GET.get("toDate", '01/01/2100')
    if from_date and to_date:
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y')

        object_list = BidFile.objects.filter(Q(project__icontains=search)
                                             | Q(customer__company__name__icontains=search))\
            .filter(due_date__range=(from_date_obj, to_date_obj)).filter(archive=False).order_by(ordering)

    else:
        object_list = BidFile.objects.filter(Q(project__icontains=search)
                                             | Q(customer__company__name__icontains=search))\
            .filter(archive=False).order_by(ordering)

    total_rows = object_list.count()

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    bidfiles = paginator.get_page(page)

    parameters = {'bidfiles': bidfiles,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'total_rows': total_rows,
                  }
    return render(request, "bfmList.html", parameters)


@login_required
def bidfiles_add(request):
    form = BidFileForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('bidFilesHome')
        files = request.FILES.getlist('uploaded_file')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                form.save()
                return redirect('bidFilesHome')
    parameters = {'form': form,
                  }
    return render(request, "bfmAdd.html", parameters)


@login_required
def bidfiles_archive(request, bidfiles_id):
    this_bidfile = get_object_or_404(BidFile, id=bidfiles_id)
    if request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by == request.user:
        if request.POST.get("confirm"):
            this_bidfile.archive = True
            this_bidfile.save()
        return redirect('bidFilesHome')
    elif request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_bidfile': this_bidfile,
                'error_msg': error_msg
            }
            return render(request, "bfmArchive.html", parameters)
        return redirect('bidFilesHome')
    parameters = {'this_bidfile': this_bidfile
                  }
    return render(request, "bfmArchive.html", parameters)


@login_required
def bidfiles_delete(request, bidfiles_id):
    this_bidfile = get_object_or_404(BidFile, id=bidfiles_id)
    if request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by == request.user:
        if request.POST.get("confirm"):
            this_bidfile.uploaded_file.delete()
            this_bidfile.delete()
        return redirect('bidFilesHome')
    elif request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_bidfile': this_bidfile,
                'error_msg': error_msg
            }
            return render(request, "bfmDelete.html", parameters)
        return redirect('bidFilesHome')
    parameters = {'this_bidfile': this_bidfile
                  }
    return render(request, "bfmDelete.html", parameters)

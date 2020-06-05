import datetime

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from mysite.pdfminer import pdfminer
from .forms import BidFileForm, BidFileEditForm
from .models import iBidFile
from ..settings import MEDIA_URL, WEB_URL, MAX_UPLOAD_SIZE


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
        to_date_obj = to_date_obj + datetime.timedelta(hours=23, minutes=59, seconds=59)

        object_list = iBidFile.objects.filter(Q(project__name__icontains=search)
                                              | Q(customer__company__name__icontains=search)) \
            .filter(due_date__range=(from_date_obj, to_date_obj)).filter(archive=False).order_by(ordering)

    else:
        object_list = iBidFile.objects.filter(Q(project__name__icontains=search)
                                              | Q(customer__company__name__icontains=search)) \
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
    return render(request, "ibfmList.html", parameters)


@login_required
def bidfiles_add(request):
    form = BidFileForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('ibidFilesHome')
        if form.is_valid():
            if request.POST.get("next"):
                files_list = request.FILES.getlist('uploaded_file')
                files = []
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'error_msg': error_msg
                    }
                    return render(request, "ibfmAdd.html", parameters)
                form.cleaned_data['created_by'] = request.user
                # b = Project(name=form.cleaned_data['project_name'], created_by=request.user)
                # b.save()
                entry = form.save()
                return redirect('ibidFilesHome')
    parameters = {'form': form,
                  }
    return render(request, "ibfmAdd.html", parameters)


@login_required
def bidfiles_edit(request, bidfiles_id):
    this_bfm = get_object_or_404(iBidFile, id=bidfiles_id)
    form = BidFileEditForm(request.POST or None, request.FILES or None, instance=this_bfm)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('ibidFilesHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('ibidFilesHome')
    parameters = {'form': form,
                  }
    return render(request, "ibfmEdit.html", parameters)


@login_required
def bidfiles_archive(request, bidfiles_id):
    this_bidfile = get_object_or_404(iBidFile, id=bidfiles_id)
    if request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by == request.user:
        if request.POST.get("confirm"):
            this_bidfile.archive = True
            this_bidfile.save()
        return redirect('ibidFilesHome')
    elif request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_bidfile': this_bidfile,
                'error_msg': error_msg
            }
            return render(request, "ibfmArchive.html", parameters)
        return redirect('ibidFilesHome')
    parameters = {'this_bidfile': this_bidfile
                  }
    return render(request, "ibfmArchive.html", parameters)


@login_required
def bidfiles_delete(request, bidfiles_id):
    this_bidfile = get_object_or_404(iBidFile, id=bidfiles_id)
    if request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by == request.user:
        if request.POST.get("confirm"):
            this_bidfile.uploaded_file.delete()
            this_bidfile.delete()
        return redirect('ibidFilesHome')
    elif request.method == "POST" and request.user.is_authenticated and this_bidfile.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_bidfile': this_bidfile,
                'error_msg': error_msg
            }
            return render(request, "ibfmDelete.html", parameters)
        return redirect('ibidFilesHome')
    parameters = {'this_bidfile': this_bidfile
                  }
    return render(request, "ibfmDelete.html", parameters)


@login_required
def pdfminer_result_page(request, bidfiles_id):
    this_bfm = get_object_or_404(iBidFile, id=bidfiles_id)
    pdfminer_result = pdfminer('/home/dtabtech/public_html' + this_bfm.uploaded_file.url, this_bfm.project.name)
    pdfminer_result[1] = pdfminer_result[1].replace('\n', ' ')
    parameters = {'pdfminer_result': pdfminer_result[1],
                  }
    return render(request, "ibfmPDFMiner.html", parameters)

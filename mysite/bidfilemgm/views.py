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
from mysite.core.models import Project
import zipfile
from io import BytesIO
import os

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

        object_list = BidFile.objects.filter(Q(project__name__icontains=search)
                                             | Q(customer__company__name__icontains=search))\
            .filter(due_date__range=(from_date_obj, to_date_obj)).filter(archive=False).order_by(ordering)

    else:
        object_list = BidFile.objects.filter(Q(project__name__icontains=search)
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
    def handle_uploaded_file(f, file_path):
        destination = open(file_path, 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

    def create_zip_file(filenames, path, project_name):
        zip_filename = os.path.join(path, project_name)
        zf = zipfile.ZipFile(zip_filename, "w")
        for file in filenames:
            fdir, fname = os.path.split(file)
            zf.write(file, fname)
            os.remove(file)
        zf.close()
        return zf
    form = BidFileForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('bidFilesHome')
        if form.is_valid():
            if request.POST.get("next"):
                temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/bidfiles")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                files_list = request.FILES.getlist('uploaded_file')
                files = []
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    handle_uploaded_file(f, files[-1])
                form.cleaned_data['created_by'] = request.user
                b = Project(name=form.cleaned_data['project_name'], created_by=request.user)
                b.save()
                entry = form.save(commit=False)
                entry.project = Project.objects.get(id=b.pk)
                entry.save()
                zip_file_name = str(entry.pk) + '. ' + form.cleaned_data['project_name'] + '.zip'
                myzip = create_zip_file(files, temp_path, zip_file_name)
                os.remove(BidFile.objects.get(id=entry.pk).uploaded_file.path)
                BidFile.objects.filter(id=entry.pk).update(uploaded_file=myzip.filename)
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

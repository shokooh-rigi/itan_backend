import datetime
import os
import zipfile

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import BidFileForm, BidFileEditForm, Person
from .models import BidFile
from ..settings import MEDIA_URL, WEB_URL, UPLOAD_URL, MAX_UPLOAD_SIZE
from django.core.files import File
from io import BytesIO
from ..s3_file_manager import S3
import requests
import os
from copy import deepcopy

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

        object_list = BidFile.objects.filter(Q(project__name__icontains=search)
                                             | Q(customer__company__name__icontains=search)) \
            .filter(due_date__range=(from_date_obj, to_date_obj)).filter(archive=False).order_by(ordering)

    else:
        object_list = BidFile.objects.filter(Q(project__name__icontains=search)
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
    return render(request, "bfmList.html", parameters)


@login_required
def bidfiles_add(request):
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
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'error_msg': error_msg
                    }
                    return render(request, "bfmAdd.html", parameters)
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    handle_uploaded_file(f, files[-1])
                form.cleaned_data['created_by'] = request.user
                form.uploaded_file = None
                # b = Project(name=form.cleaned_data['project_name'], created_by=request.user)
                # b.save()
                entry = form.save()
                project_clean_name = form.cleaned_data['project'].name.replace(' ', '_') \
                    .replace('!', '') \
                    .replace('@', '') \
                    .replace('#', '') \
                    .replace('$', '') \
                    .replace('%', '') \
                    .replace('^', '') \
                    .replace('&', '') \
                    .replace('*', '') \
                    .replace("/", '')
                zip_file_name = str(entry.pk) + '. ' + project_clean_name + '.zip'
                zf = create_zip_file(files, temp_path, zip_file_name)
                s3 = S3()
                if BidFile.objects.get(id=entry.pk).uploaded_file:
                    s3.delete_file_from_bucket(key=MEDIA_URL + str(BidFile.objects.get(id=entry.pk).uploaded_file))
                file = open(temp_path + '/' + zip_file_name, 'rb')
                BidFile.objects.get(id=entry.pk).uploaded_file.save(zip_file_name, file)
                os.remove(temp_path + '/' + zip_file_name)
                return redirect('bidFilesHome')
    parameters = {'form': form,
                  }
    return render(request, "bfmAdd.html", parameters)


@login_required
def bidfiles_addfile(request, bidfiles_id):
    this_bfm = get_object_or_404(BidFile, id=bidfiles_id)
    form = BidFileEditForm(request.POST or None, request.FILES or None, instance=this_bfm)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('bidFilesHome')
        if request.POST.get("next"):
            temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/bidfiles")
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
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
                return render(request, "bfmAdd.html", parameters)
            for f in files_list:
                files.append(os.path.join(temp_path, f.name))
                handle_uploaded_file(f, files[-1])
            # b = Project(name=form.cleaned_data['project_name'], created_by=request.user)
            # b.save()
            entry = form
            project_clean_name = this_bfm.project.name.replace(' ', '_') \
                .replace('!', '') \
                .replace('@', '') \
                .replace('#', '') \
                .replace('$', '') \
                .replace('%', '') \
                .replace('^', '') \
                .replace('&', '') \
                .replace('*', '') \
                .replace("/", '')
            zip_file_name = str(this_bfm.pk) + '. ' + project_clean_name + '.zip'
            s3 = S3()
            response = requests.get(s3.get_bucket_object('media/' + str(this_bfm.uploaded_file.file)))
            f = open(os.path.join(temp_path, zip_file_name), 'wb')
            f.write(response.content)
            f.close()
            addto_zip_file(files, temp_path, zip_file_name)
            if BidFile.objects.get(id=this_bfm.pk).uploaded_file:
                s3.delete_file_from_bucket(key=MEDIA_URL + str(BidFile.objects.get(id=this_bfm.pk).uploaded_file))
            file = open(temp_path + '/' + zip_file_name, 'rb')
            BidFile.objects.get(id=this_bfm.pk).uploaded_file.save(zip_file_name, file)
            os.remove(temp_path + '/' + zip_file_name)
            return redirect('bidFilesHome')
        else:
            print(request)
    parameters = {'form': form,
                  }
    return render(request, "bfmAddFile.html", parameters)


@login_required
def bidfiles_edit(request, bidfiles_id):
    this_bfm = get_object_or_404(BidFile, id=bidfiles_id)
    form = BidFileEditForm(request.POST or None, request.FILES or None, instance=this_bfm)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('bidFilesHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('bidFilesHome')
    parameters = {'form': form,

                  }
    return render(request, "bfmEdit.html", parameters)


@login_required
def bidfiles_duplicate(request, bidfiles_id):
    this_bidfile = get_object_or_404(BidFile, id=bidfiles_id)
    form = BidFileForm(request.POST or None, instance=this_bidfile)
    form.fields['project'].widget = forms.HiddenInput()
    form.fields['uploaded_file'].widget = forms.HiddenInput()
    form.fields['due_date'].widget = forms.HiddenInput()
    form.fields['note'].widget = forms.HiddenInput()

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('bidFilesHome')
        if request.POST.get("next"):
            duplicated_bfm = deepcopy(this_bidfile)
            duplicated_bfm.id = None
            duplicated_bfm.uploaded_file = None
            duplicated_bfm.customer = Person.objects.get(id=request.POST.get("customer"))
            duplicated_bfm.created_by = request.user
            duplicated_bfm.save()
            return redirect('bidFilesHome')

    parameters = {
        'form': form,
    }
    return render(request, "bfmDuplicate.html", parameters)


@login_required
def bidfiles_archive(request, bidfiles_id):
    this_bidfile = get_object_or_404(BidFile, id=bidfiles_id)
    if request.method == "POST":
        if request.POST.get("confirm"):
            if request.user.is_authenticated:
                if this_bidfile.created_by == request.user or request.user.profile.user_type == 2:
                    this_bidfile.archive = True
                    this_bidfile.save()
                    return redirect('bidFilesHome')
                else:
                    error_msg = "This record was created by another user, you are not authorized to delete this record."
                    parameters = {
                        'this_bidfile': this_bidfile,
                        'error_msg': error_msg
                    }
                    return render(request, "bfmArchive.html", parameters)
            return redirect('bidFilesHome')
        else:
            return redirect('bidFilesHome')
    parameters = {
        'this_bidfile': this_bidfile
    }
    return render(request, "bfmArchive.html", parameters)


@login_required
def bidfiles_delete(request, bidfiles_id):
    this_bidfile = get_object_or_404(BidFile, id=bidfiles_id)
    if request.method == "POST":
        if request.POST.get("confirm"):
            if request.user.is_authenticated:
                if this_bidfile.created_by == request.user or request.user.profile.user_type == 2:
                    s3 = S3()
                    s3.delete_file_from_bucket(key=MEDIA_URL + str(this_bidfile.uploaded_file))
                    this_bidfile.delete()
                    return redirect('bidFilesHome')
                else:
                    error_msg = "This record was created by another user, you are not authorized to delete this record."
                    parameters = {
                        'this_bidfile': this_bidfile,
                        'error_msg': error_msg
                    }
                    return render(request, "bfmDelete.html", parameters)
            return redirect('bidFilesHome')
        else:
            return redirect('bidFilesHome')
    parameters = {'this_bidfile': this_bidfile
                  }
    return render(request, "bfmDelete.html", parameters)


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


def addto_zip_file(filenames, path, project_name):
    zip_filename = os.path.join(path, project_name)
    zf = zipfile.ZipFile(zip_filename, "a")
    for file in filenames:
        fdir, fname = os.path.split(file)
        zf.write(file, fname)
        os.remove(file)
    zf.close()
    return zf


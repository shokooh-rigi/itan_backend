from django.contrib.auth.decorators import login_required, permission_required
from .forms import AdministrativeForm
from .models import Document
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, UPLOAD_URL, MAX_UPLOAD_SIZE
from django import forms
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.


@permission_required('administrative.view_document')
@login_required
def documents_list(request):
    search = request.GET.get('search', '')
    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    object_list = Document.objects.filter(customer__name__icontains=search)
    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    documents = paginator.get_page(page)

    parameters = {'documents': documents,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "documentList.html", parameters)


@permission_required('administrative.add_document')
@login_required
def documents_add(request):
    form = AdministrativeForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('administrativeHome')
        if form.is_valid():
            if request.POST.get("next"):
                files_list = request.FILES.getlist('uploaded_file')
                size_sum = 0
                for f in files_list:
                    size_sum = size_sum + f.size
                if size_sum > MAX_UPLOAD_SIZE:
                    error_msg = "Selected files exceeded maximum upload size!"
                    parameters = {
                        'form': form,
                        'error_msg': error_msg
                    }
                    return render(request, "documentAdd.html", parameters)
                form.cleaned_data['created_by'] = request.user
                form.save()
                return redirect('administrativeHome')
    parameters = {'form': form,
                  }
    return render(request, "documentAdd.html", parameters)


@permission_required('administrative.change_document')
@login_required
def document_edit(request, document_id):
    this_document = get_object_or_404(Document, id=document_id)
    form = AdministrativeForm(request.POST or None, request.FILES or None, instance=this_document)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('administrativeHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('administrativeHome')
    parameters = {'form': form,
                  }
    return render(request, "documentEdit.html", parameters)


@permission_required('administrative.delete_document')
@login_required
def document_delete(request, document_id):
    this_document = get_object_or_404(Document, id=document_id)
    if request.method == "POST" and request.user.is_authenticated and this_document.created_by == request.user:
        if request.POST.get("confirm"):
            this_document.uploaded_file.delete()
            this_document.delete()
        return redirect('administrativeHome')
    elif request.method == "POST" and request.user.is_authenticated and this_document.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_document': this_document,
                'error_msg': error_msg
            }
            return render(request, "bfmDelete.html", parameters)
        return redirect('bidFilesHome')
    parameters = {'this_document': this_document
                  }
    return render(request, "documentDelete.html", parameters)

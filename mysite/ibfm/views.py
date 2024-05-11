import pickle
import json
import time
import datetime

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

# from mysite.pdf_analyzer.pdf_analyzer import start_find_project_address
from mysite.pdf_analyzer.models import AddressExtractionRun, AddressExtractionDebug
from mysite.pdf_analyzer.src.logger.logger_models import ADDRESS_RUN_STEPS

from .forms import BidFileForm, BidFileEditForm
from .models import iBidFile
from django.conf import settings


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
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
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
                if size_sum > settings.MAX_UPLOAD_SIZE:
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


########################################################################################################################
# PDF Analyzer
# find project address
@login_required()
def pdf_analyzer_project_address_run(request, bidfile_id):
    bidfile = get_object_or_404(iBidFile, pk=bidfile_id)

    active_runs = AddressExtractionRun.objects.filter(file=bidfile, is_finished=False)
    if active_runs.exists():
        return redirect('ibidFilesPDFAnalyzerProjectAddressProgress', active_runs.first().pk)

    return None

    run_id = start_find_project_address(bidfile, bidfile.project.name)
    return redirect('ibidFilesPDFAnalyzerProjectAddressProgress', run_id)


@login_required()
def pdf_analyzer_project_address_progress_json(request, run_id):
    run = get_object_or_404(AddressExtractionRun, pk=run_id)
    parameters = {
        'is_finished': run.is_finished,
        'run_step': run.run_step,
        'run_step_progress': run.run_step_progress,
        'elapsed_time': int(time.time() - run.created_on.timestamp()),
    }
    return JsonResponse(parameters)


@login_required()
def pdf_analyzer_project_address_progress_json_all(request, run_id):
    run = get_object_or_404(AddressExtractionRun, pk=run_id)
    parameters = {
        'pdf_file': run.file.uploaded_file.url,
        'project_name': run.project_name,
        'is_finished': run.is_finished,
        'run_step': run.run_step,
        'run_step_progress': run.run_step_progress,
        'elapsed_time': int(time.time() - run.created_on.timestamp()),
        'steps': ADDRESS_RUN_STEPS,
    }
    return JsonResponse(parameters)


@login_required()
def pdf_analyzer_project_address_progress(request, run_id):
    run = get_object_or_404(AddressExtractionRun, pk=run_id)
    if run.is_finished:
        return redirect('ibidFilesPDFAnalyzerProjectAddressDebug', run_id)

    parameters = {'run_id': run_id}
    return render(request, "ibfmPDFAnalyzerProjectAddressProgress.html", parameters)


def save_address_extraction_debug(request, run: AddressExtractionRun):
    data = [
        {
            'address_is_correct': request.POST.get('step_1_address_is_correct') == 'on',
            'correct_address': request.POST.get('step_1_correct_address', '').strip(),
            'description': request.POST.get('step_1_description', '').strip(),
        },
        {
            'project_name_is_in_boxes': request.POST.get('step_2_project_name_is_in_boxes', 'true'),
            'project_address_is_in_boxes': request.POST.get('step_2_project_address_is_in_boxes', 'true'),
            'description': request.POST.get('step_2_description', '').strip(),
        },
        {
            'project_name_is_in_boxes': request.POST.get('step_3_project_name_is_in_boxes', 'true'),
            'project_address_is_in_boxes': request.POST.get('step_3_project_address_is_in_boxes', 'true'),
            'description': request.POST.get('step_3_description', '').strip(),
        },
        {
            'project_name_is_correct': request.POST.get('step_4_project_name_is_correct', 'true'),
            'project_address_is_correct': request.POST.get('step_4_project_address_is_correct', 'true'),
            'description': request.POST.get('step_4_description', '').strip(),
        },
        {
            'project_name_is_in_similar_lines': request.POST.get('step_5_project_name_is_in_similar_lines', 'true'),
            'description': request.POST.get('step_5_description', '').strip(),
        },
        {
            'boxes_below_lines_are_correct': request.POST.get('step_6_boxes_below_lines_are_correct', 'true'),
            'project_address_is_in_boxes': request.POST.get('step_6_project_address_is_in_boxes', 'true'),
            'description': request.POST.get('step_6_description', '').strip(),
        },
        {
            'text_blocks_are_correct': request.POST.get('step_7_text_blocks_are_correct', 'true'),
            'project_address_is_in_one_block': request.POST.get('step_7_project_address_is_in_one_block', 'true'),
            'project_address_has_extra_text': request.POST.get('step_7_project_address_has_extra_text', 'false'),
            'description': request.POST.get('step_7_description', '').strip(),
        },
    ]

    if data[0]['address_is_correct'] and run.file.created_by == request.user:
        run.file.archive = True
        run.file.save()

    for i in range(7):
        debug = AddressExtractionDebug(run=run, debug_step=i + 1, data=json.dumps(data[i]))
        debug.save()


@login_required()
def pdf_analyzer_project_address_debug_json(request, run_id):
    run = get_object_or_404(AddressExtractionRun, pk=run_id)

    with open(run.process_variables, 'rb') as vars_file:
        process_variables = pickle.load(vars_file)

    parameters = {
        'run_id': run_id,
        'pdf_file': run.file.uploaded_file.url,
        'project_name': run.project_name,
        'processed_images': json.loads(run.get_processed_images_url()),
        'process_variables': process_variables,
        'addresses': json.loads(run.addresses),
        'execution_time': run.execution_time,
        'created_on': run.created_on,
        'debug_data': None,
    }

    if run.addressextractiondebug_set.exists():
        debug_data = []
        debug_steps = run.addressextractiondebug_set.all()
        for step in debug_steps:
            debug_data.append(json.loads(step.data))
        parameters['debug_data'] = debug_data

    return JsonResponse(parameters)


@login_required()
def pdf_analyzer_project_address_debug(request, run_id):
    run = get_object_or_404(AddressExtractionRun, pk=run_id)
    if not run.is_finished:
        return redirect('ibidFilesPDFAnalyzerProjectAddressProgress', run_id)

    parameters = {'run_id': run_id}
    if not run.addressextractiondebug_set.exists() and request.method == 'POST':
        save_address_extraction_debug(request, run)
    return render(request, "ibfmPDFAnalyzerProjectAddressDebug.html", parameters)


@login_required
def pdf_analyzer_project_address_report(request):
    page = request.GET.get('page')
    search = request.GET.get('search', '').strip()
    pagination = request.GET.get('paginate_by') or 20
    ordering = request.GET.get('ordering') or 'project_name'
    from_date = request.GET.get('fromDate') or '01/01/2000'
    to_date = request.GET.get('toDate') or '01/01/2100'

    from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
    to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y') + datetime.timedelta(hours=23, minutes=59, seconds=59)

    object_list = AddressExtractionRun.objects.filter(is_finished=True) \
        .filter(Q(project_name__icontains=search) | Q(file__uploaded_file__icontains=search)) \
        .filter(created_on__range=(from_date_obj, to_date_obj)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    parameters = {
        'runs': paginator.get_page(page),
        'total_rows': object_list.count(),
    }
    return render(request, 'ibfmPDFAnalyzerProjectAddressReport.html', parameters)
########################################################################################################################

import datetime
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django import forms
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from ..estimator.views import estimate_total_work
from ..scheduler.models import Maintenance, Schedule, ScheduleTech, LicenseFiles
from ..sheetcreator.models import Sheet
import os
import zipfile
from ..settings import MEDIA_URL, WEB_URL, UPLOAD_URL, MAX_UPLOAD_SIZE
from ..bidfilemgm.views import handle_uploaded_file, create_zip_file, addto_zip_file
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..order.templatetags.order_tags import order_tech_final_price_calculator, order_tech_predemo_price_calculator
from ..core.models import Setting
from ..s3_file_manager import S3
import requests
import os


# Create your views here.


@login_required
def tech_calendar(request):
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    parameters = {
        'current_user': request.user,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
        'owner_logo': owner_logo,
        'STATIC_URL': STATIC_URL,
    }
    return render(request, "schedule2.html", parameters)


@login_required
def schedule_list(request):
    schedule_start_date = Setting.objects.get(key='Schedule Start Date').value
    schedule_start_date = datetime.datetime.strptime(schedule_start_date, "%m/%d/%Y").date()
    if request.user.profile.status == 1:
        maintenance_list = Maintenance.objects.filter(assigned_to_employee=request.user).filter(schedule_start__gte=schedule_start_date)
        scheduled = Schedule.objects.filter(scheduletech__assigned_to_employee=request.user).filter(schedule_start__gte=schedule_start_date)
    elif request.user.profile.status == 2:
        maintenance_list = Maintenance.objects.filter(assigned_to_contractor=request.user).filter(schedule_start__gte=schedule_start_date)
        scheduled = Schedule.objects.filter(scheduletech__assigned_to_contractor=request.user).filter(schedule_start__gte=schedule_start_date)
    else:
        maintenance_list = None
        scheduled = None
    response_data = []
    for schedule in scheduled:
        if request.user.profile.status == 1:
            this_schedule_tech = ScheduleTech.objects.get(schedule=schedule, assigned_to_employee=request.user)
        elif request.user.profile.status == 2:
            this_schedule_tech = ScheduleTech.objects.get(schedule=schedule, assigned_to_contractor=request.user)
        else:
            this_schedule_tech = None
        full_address = ''
        if schedule.order.proposal.quote.estimate.project.address_line_1:
            full_address += schedule.order.proposal.quote.estimate.project.address_line_1
        if schedule.order.proposal.quote.estimate.project.address_line_2:
            full_address += ' ' + schedule.order.proposal.quote.estimate.project.address_line_2
        if schedule.order.proposal.quote.estimate.project.city:
            full_address += ' ' + schedule.order.proposal.quote.estimate.project.city
        if schedule.order.proposal.quote.estimate.project.state:
            full_address += ' ' + schedule.order.proposal.quote.estimate.project.state
        if schedule.order.proposal.quote.estimate.project.zip:
            full_address += ' ' + schedule.order.proposal.quote.estimate.project.zip

        # if schedule.assigned_to_employee:
        #     calendar_id = schedule.assigned_to_employee.id
        # else:
        #     calendar_id = 0
        assigned_to_employees = []
        assigned_to_employees_names = []
        assigned_to_contractors = []
        assigned_to_contractors_names = []
        tech_file = None
        for schedule_tech in ScheduleTech.objects.filter(schedule=schedule).all():

            if schedule_tech.assigned_to_employee:

                if schedule_tech.assigned_to_employee.id == request.user.id:
                    if schedule_tech.tech_upload:
                        tech_file = schedule_tech.tech_upload.url

                assigned_to_employees.append(schedule_tech.assigned_to_employee.id)
                if schedule_tech.assigned_to_employee.last_name:
                    assigned_to_employees_names.append(
                        schedule_tech.assigned_to_employee.first_name + ' ' + schedule_tech.assigned_to_employee.last_name)
                else:
                    assigned_to_employees_names.append(schedule_tech.assigned_to_employee.email)
            elif schedule_tech.assigned_to_contractor:

                if schedule_tech.assigned_to_contractor.id == request.user.id:
                    if schedule_tech.tech_upload:
                        tech_file = schedule_tech.tech_upload.url

                assigned_to_contractors.append(schedule_tech.assigned_to_contractor.id)
                if schedule_tech.assigned_to_contractor.last_name:
                    assigned_to_contractors_names.append(schedule_tech.assigned_to_contractor.first_name + ' ' + schedule_tech.assigned_to_contractor.last_name)
                else:
                    assigned_to_contractors_names.append(schedule_tech.assigned_to_contractor.email)
        any_assigned = False
        if ScheduleTech.objects.filter(schedule=schedule).count() > 0:
            any_assigned = True
        poc_name = ''
        poc_cell_phone = ''
        poc_office_phone = ''
        special_instruction = ''
        equipment_submittal = ''
        test_sheets = ''
        tech_marked_drawing = ''
        site_pictures = ''
        cs_file = ''
        try:
            poc_name = schedule.order.techlabel.point_of_contact_name
            special_instruction = schedule.order.techlabel.tech_notes
            if schedule.order.techlabel.point_of_contact_cell_phone:
                poc_cell_phone = schedule.order.techlabel.point_of_contact_cell_phone
            if schedule.order.techlabel.point_of_contact_office_phone:
                poc_office_phone = schedule.order.techlabel.point_of_contact_office_phone
            if schedule.order.control_system:
                if schedule.order.control_system.control_file_url:
                    cs_file = schedule.order.control_system.control_file_url
            if schedule.order.equipment_submittal:
                equipment_submittal = schedule.order.equipment_submittal.url
            if schedule.order.test_sheets:
                test_sheets = schedule.order.test_sheets.url
            if schedule.order.tech_marked_drawing:
                tech_marked_drawing = schedule.order.tech_marked_drawing.url
            if schedule.order.site_pictures:
                site_pictures = schedule.order.site_pictures.url
        except:
            pass
        test_sheet_id = ''
        test_sheet_count = Sheet.objects.filter(project__id=schedule.order.id).count()
        if test_sheet_count > 0:
            test_sheet_id = Sheet.objects.get(project__id=schedule.order.id).id
        response_data.append({
            'order_id': str(schedule.order.id),
            'schedule_id': str(schedule.id),
            'assigned_to_employees': assigned_to_employees,
            'assigned_to_contractors': assigned_to_contractors,
            'assigned_to_employees_names': assigned_to_employees_names,
            'assigned_to_contractors_names': assigned_to_contractors_names,
            'tech_file': tech_file,
            'project_number': schedule.order.project_number,
            'project_name': str(schedule.order.proposal.quote.estimate.project),
            'customer': str(schedule.order.proposal.quote.estimate.customer.company.name),
            'engineer': str(schedule.order.proposal.quote.estimate.engineer.company.name),
            'predemo': schedule.order.proposal.quote.estimate.estimatedetails.pre_demo,
            'poc_name': poc_name,
            'poc_cell_phone': poc_cell_phone,
            'poc_office_phone': poc_office_phone,
            'control_system': str(schedule.order.control_system),
            'special_instruction': special_instruction,
            'tech_note': this_schedule_tech.note,
            'price': order_tech_predemo_price_calculator(schedule.order.proposal.quote.estimate.id, schedule.order) if schedule.pre_demo else order_tech_final_price_calculator(schedule.order.proposal.quote.estimate.id, schedule.order),
            'equipment_submittals_link': equipment_submittal,
            'test_sheets_link': test_sheets,
            'tech_marked_drawing_link': tech_marked_drawing,
            'site_pictures_link': site_pictures,
            'cs_software_link': cs_file,
            'title': str(schedule.order.proposal.quote.estimate.project),
            'assigned': any_assigned,
            'location': full_address,
            'category': 'time',
            'start': schedule.schedule_start,
            'end': schedule.schedule_end,
            'estimate': estimate_total_work(schedule.order.proposal.quote.estimate.id),
            'goingDuration': str(30),
            'comingDuration': str(30),
            'partial': schedule.order.partial_job_done,
            'test_sheet_id': test_sheet_id
        })

    for maintenance in maintenance_list:
        full_address = ''
        if maintenance.order:
            if maintenance.order.proposal.quote.estimate.project.address_line_1:
                full_address += maintenance.order.proposal.quote.estimate.project.address_line_1
            if maintenance.order.proposal.quote.estimate.project.address_line_2:
                full_address += ' ' + maintenance.order.proposal.quote.estimate.project.address_line_2
            if maintenance.order.proposal.quote.estimate.project.city:
                full_address += ' ' + maintenance.order.proposal.quote.estimate.project.city
            if maintenance.order.proposal.quote.estimate.project.state:
                full_address += ' ' + maintenance.order.proposal.quote.estimate.project.state
            if maintenance.order.proposal.quote.estimate.project.zip:
                full_address += ' ' + maintenance.order.proposal.quote.estimate.project.zip
        assigned_to_employees = []
        assigned_to_employees_names = []
        assigned_to_contractors = []
        assigned_to_contractors_names = []
        if maintenance.assigned_to_employee:
            assigned_to_employees.append(maintenance.assigned_to_employee.id)
            if maintenance.assigned_to_employee.last_name:
                assigned_to_employees_names.append(maintenance.assigned_to_employee.first_name + ' ' + maintenance.assigned_to_employee.last_name)
            else:
                assigned_to_employees_names.append(maintenance.assigned_to_employee.email)
        elif maintenance.assigned_to_contractor:
            assigned_to_contractors.append(maintenance.assigned_to_contractor.id)
            if maintenance.assigned_to_contractor.last_name:
                assigned_to_contractors_names.append(maintenance.assigned_to_contractor.first_name + ' ' + maintenance.assigned_to_contractor.last_name)
            else:
                assigned_to_contractors_names.append(maintenance.assigned_to_contractor.email)
        any_assigned = False
        if maintenance.assigned_to_employee or maintenance.assigned_to_contractor:
            any_assigned = True
        details_completed = False
        if maintenance.order and any_assigned:
            details_completed = True
        maintenance_order_id = ''
        maintenance_title = 'Maintenance'
        if maintenance.maintenance_type == 2:
            maintenance_title = 'Lost Time'
        elif maintenance.maintenance_type == 3:
            maintenance_title = 'Off/Vacation'
        if maintenance.order:
            if maintenance.maintenance_type == 1:
                maintenance_title = 'Maintenance ' + str(maintenance.order.project_number + '<br />' + str(maintenance.order.proposal.quote.estimate.project))
            else:
                maintenance_title = 'Lost Time ' + str(maintenance.order.project_number + '<br />' + str(maintenance.order.proposal.quote.estimate.project))
            maintenance_order_id = maintenance.order.id

        poc_name = ''
        poc_cell_phone = ''
        poc_office_phone = ''
        special_instruction = ''
        equipment_submittal = ''
        test_sheets = ''
        tech_marked_drawing = ''
        site_pictures = ''
        cs_file = ''
        try:
            poc_name = maintenance.order.techlabel.point_of_contact_name
            special_instruction = maintenance.order.techlabel.tech_notes
            if maintenance.order.techlabel.point_of_contact_cell_phone:
                poc_cell_phone = maintenance.order.techlabel.point_of_contact_cell_phone
            if maintenance.order.techlabel.point_of_contact_office_phone:
                poc_office_phone = maintenance.order.techlabel.point_of_contact_office_phone
            if maintenance.order.control_system:
                if maintenance.order.control_system.control_file_url:
                    cs_file = maintenance.order.control_system.control_file_url
            if maintenance.order.equipment_submittal:
                equipment_submittal = maintenance.order.equipment_submittal.url
            if maintenance.order.test_sheets:
                test_sheets = maintenance.order.test_sheets.url
            if maintenance.order.tech_marked_drawing:
                tech_marked_drawing = maintenance.order.tech_marked_drawing.url
            if maintenance.order.site_pictures:
                site_pictures = maintenance.order.site_pictures.url
        except:
            pass
        test_sheet_id = ''
        test_sheet_count = 0
        if maintenance.order:
            test_sheet_count = Sheet.objects.filter(project__id=maintenance.order.id).count()
        if test_sheet_count > 0:
            test_sheet_id = Sheet.objects.get(project__id=maintenance.order.id).id

        if maintenance.maintenance_type == 1:
            bg_color = '#ffc107' if details_completed else '#6c757d'
            color = '#000' if details_completed else '#fff'
        elif maintenance.maintenance_type == 2:
            bg_color = '#b82634' if details_completed else '#6c757d'
            color = '#fff'
        else:
            bg_color = '#000'
            color = '#fff'
        response_data.append({
            'order_id': maintenance_order_id,
            'maintenance_id': str(maintenance.id),
            'maintenance_type': maintenance.maintenance_type,
            'assigned_to_employees': assigned_to_employees,
            'assigned_to_contractors': assigned_to_contractors,
            'assigned_to_employees_names': assigned_to_employees_names,
            'assigned_to_contractors_names': assigned_to_contractors_names,
            'project_number': maintenance.order.project_number if maintenance.order else 0,
            'project_name': str(maintenance.order.proposal.quote.estimate.project) if maintenance.order else '',
            'customer': str(maintenance.order.proposal.quote.estimate.customer.company.name) if maintenance.order else '',
            'engineer': str(maintenance.order.proposal.quote.estimate.engineer.company.name) if maintenance.order else '',
            'predemo': maintenance.order.proposal.quote.estimate.estimatedetails.pre_demo if maintenance.order else 0,
            'poc_name': poc_name,
            'poc_cell_phone': poc_cell_phone,
            'poc_office_phone': poc_office_phone,
            'control_system': str(maintenance.order.control_system) if maintenance.order else '',
            'special_instruction': special_instruction,
            'tech_note': maintenance.note,
            'price': 0,
            'equipment_submittals_link': equipment_submittal,
            'test_sheets_link': test_sheets,
            'tech_marked_drawing_link': tech_marked_drawing,
            'site_pictures_link': site_pictures,
            'cs_software_link': cs_file,
            'title': maintenance_title,
            'assigned': any_assigned,
            'location': full_address,
            'category': 'time',
            'start': maintenance.schedule_start,
            'end': maintenance.schedule_end,
            'goingDuration': str(30),
            'comingDuration': str(30),
            'completed': details_completed,
            'bg_color': bg_color,
            'color': color,
            'test_sheet_id': test_sheet_id
        })
    return JsonResponse(response_data, safe=False)


@login_required
def update_note(request):
    if request.method == "POST" and request.is_ajax():
        if request.POST.get('schedule_id'):
            schedule_id = request.POST.get('schedule_id')
            note = request.POST.get('note_text')
            if request.user.profile.status == 1:
                schedule_update = get_object_or_404(ScheduleTech, schedule__id=schedule_id, assigned_to_employee=request.user)
            else:
                schedule_update = get_object_or_404(ScheduleTech, schedule__id=schedule_id, assigned_to_contractor=request.user)
            schedule_update.note = note
            schedule_update.save()
            return JsonResponse({
                'result': True,
                'msg': 'Note updated on database successfully.'
            })
        elif request.POST.get('maintenance_id'):
            maintenance_id = request.POST.get('maintenance_id')
            note = request.POST.get('note_text')
            if request.user.profile.status == 1:
                maintenance_update = get_object_or_404(Maintenance, id=maintenance_id, assigned_to_employee=request.user)
            else:
                maintenance_update = get_object_or_404(Maintenance, id=maintenance_id, assigned_to_contractor=request.user)
            maintenance_update.note = note
            maintenance_update.save()
            return JsonResponse({
                'result': True,
                'msg': 'Note updated on database successfully.'
            })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


@login_required
def upload_tech(request):
    if request.method == "POST" and request.is_ajax():
        if request.POST.get('schedule_id'):
            schedule_id = request.POST.get('schedule_id')
            if request.user.profile.status == 1:
                schedule_update = get_object_or_404(ScheduleTech, schedule__id=schedule_id, assigned_to_employee=request.user)
            else:
                schedule_update = get_object_or_404(ScheduleTech, schedule__id=schedule_id, assigned_to_contractor=request.user)

            temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/techfiles")
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
            files_list = request.FILES.getlist('upload_tech')
            files = []
            size_sum = 0
            for f in files_list:
                size_sum = size_sum + f.size
            if size_sum > MAX_UPLOAD_SIZE:
                error_msg = "Selected files exceeded maximum upload size!"
                return JsonResponse({
                    'result': False,
                    'msg': error_msg
                })
            for f in files_list:
                files.append(os.path.join(temp_path, f.name))
                handle_uploaded_file(f, files[-1])
            if request.user.last_name:
                zip_file_name = str(schedule_update.schedule.id) + '. ' + str(request.user.first_name) + ' ' + str(request.user.last_name) + '.zip'
            else:
                zip_file_name = str(schedule_update.schedule.id) + '. ' + str(request.user.email) + '.zip'

            if schedule_update.tech_upload:
                s3 = S3()
                response = requests.get(s3.get_bucket_object('media/' + str(schedule_update.tech_upload.file)))
                f = open(os.path.join(temp_path, zip_file_name), 'wb')
                f.write(response.content)
                f.close()
                addto_zip_file(files, temp_path, zip_file_name)
                s3.delete_file_from_bucket(key=MEDIA_URL + str(schedule_update.tech_upload))
                file = open(temp_path + '/' + zip_file_name, 'rb')
                schedule_update.tech_upload.save(zip_file_name, file)
                os.remove(temp_path + '/' + zip_file_name)
            else:
                create_zip_file(files, temp_path, zip_file_name)
                s3 = S3()
                file = open(temp_path + '/' + zip_file_name, 'rb')
                schedule_update.tech_upload.save(zip_file_name, file)
                os.remove(temp_path + '/' + zip_file_name)

            return JsonResponse({
                'result': True,
                'msg': 'Upload successful!'
            })
        elif request.POST.get('maintenance_id'):
            maintenance_id = request.POST.get('maintenance_id')
            if request.user.profile.status == 1:
                maintenance_update = get_object_or_404(Maintenance, id=maintenance_id, assigned_to_employee=request.user)
            else:
                maintenance_update = get_object_or_404(Maintenance, id=maintenance_id, assigned_to_contractor=request.user)

            temp_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/uploads/techfiles")
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
            files_list = request.FILES.getlist('upload_tech')
            files = []
            size_sum = 0
            for f in files_list:
                size_sum = size_sum + f.size
            if size_sum > MAX_UPLOAD_SIZE:
                msg = "Selected files exceeded maximum upload size!"
                return JsonResponse({
                    'result': False,
                    'msg': msg
                })
            for f in files_list:
                files.append(os.path.join(temp_path, f.name))
                handle_uploaded_file(f, files[-1])
            if request.user.last_name:
                zip_file_name = str(maintenance_update.id) + '. Maintenance ' + str(request.user.first_name) + ' ' + str(request.user.last_name) + '.zip'
            else:
                zip_file_name = str(maintenance_update.id) + '. Maintenance ' + str(request.user.email) + '.zip'
            if maintenance_update.tech_upload:
                addto_zip_file(files, temp_path, zip_file_name)
            else:
                create_zip_file(files, temp_path, zip_file_name)
                maintenance_update.tech_upload = UPLOAD_URL + 'techfiles/' + zip_file_name
                maintenance_update.save()

            return JsonResponse({
                'result': True,
                'msg': 'Upload successful!'
            })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)

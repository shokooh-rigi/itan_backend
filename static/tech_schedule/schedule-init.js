    let calendar = FullCalendar.Calendar;

    let myEvents = [];

    function searchAssigns(nameKey, myArray, type) {
        for (var i=0; i < myArray.length; i++) {
            if (myArray[i].id == nameKey && myArray[i].type == type) {
                return myArray[i];
            }
        }
    }

    function allowDropTech(ev) {
            ev.preventDefault();
            ev.target.classList.add("assigned");
    }

    function dropLeaveTech(ev) {
        ev.preventDefault();
        var all_assignable = document.getElementsByClassName("assignable-schedule");
        var len = all_assignable.length;
        var i = 0;
        for (i; i < len; i++) {
            all_assignable[i].classList.remove("assigned");
        }
    }

    function dragTech(ev) {
        console.log(ev)
        ev.dataTransfer.setData("type", ev.target.dataset.type);
        ev.dataTransfer.setData("id", ev.target.dataset.id);
    }


    function dropTech(ev) {
        ev.preventDefault();
        if (ev.target.closest(".fc-event").dataset.scheduleid) {
            const new_tech_id = ev.dataTransfer.getData("id");
            const org_order_id = ev.target.closest(".fc-event").dataset.id;
            const schedule_id = ev.target.closest(".fc-event").dataset.scheduleid;


            $.ajax({
                type: 'POST',
                dataType: 'json',
                url: "/schedule/update_schedule/",
                data: {
                    'type': 'tech_add',
                    'org_order_id': org_order_id,
                    'schedule_id': schedule_id,
                    'new_tech_id': new_tech_id,
                    'tech_type': ev.dataTransfer.getData("type")
                },
                success: function (response) {
                    console.log(response)
                    if (response.result == false) {
                        alert(response.err_msg);
                    } else {
                        var event = calendar.getEventById('schedule-' + schedule_id);
                        let new_employee_array = []
                        if (ev.dataTransfer.getData("type") == 'employee') {
                            if (event.extendedProps['employees'] !== undefined)
                                new_employee_array = event.extendedProps['employees']
                            if (!new_employee_array.includes(parseInt(new_tech_id)))
                                new_employee_array.push(parseInt(new_tech_id))
                            console.log(new_employee_array)
                            event.setExtendedProp('employees', new_employee_array)
                        } else {
                            if (event.extendedProps['contractors'] !== undefined)
                                new_employee_array = event.extendedProps['contractors']
                            if (!new_employee_array.includes(parseInt(new_tech_id)))
                                new_employee_array.push(parseInt(new_tech_id))
                            console.log(new_employee_array)
                            event.setExtendedProp('contractors', new_employee_array)
                        }
                        calendar.refetchEvents();
                    }
                }
            });
        } else {
            const new_tech_id = ev.dataTransfer.getData("id");
            const maintenance_id = ev.target.closest(".fc-event").dataset.maintenanceid;


            $.ajax({
                type: 'POST',
                dataType: 'json',
                url: "/schedule/update_maintenance/",
                data: {
                    'type': 'tech_add',
                    'maintenance_id': maintenance_id,
                    'new_tech_id': new_tech_id,
                    'tech_type': ev.dataTransfer.getData("type")
                },
                success: function (response) {
                    console.log(response)
                    if (response.result == false) {
                        alert(response.err_msg);
                    } else {
                        const event = calendar.getEventById('maintenance-' + maintenance_id);
                        let new_employee_array = []
                        if (ev.dataTransfer.getData("type") == 'employee') {
                            if (event.extendedProps['employees'] !== undefined)
                                new_employee_array = event.extendedProps['employees']
                            if (!new_employee_array.includes(parseInt(new_tech_id)))
                                new_employee_array.push(parseInt(new_tech_id))
                            console.log(new_employee_array)
                            event.setExtendedProp('employees', new_employee_array)
                        } else {
                            if (event.extendedProps['contractors'] !== undefined)
                                new_employee_array = event.extendedProps['contractors']
                            if (!new_employee_array.includes(parseInt(new_tech_id)))
                                new_employee_array.push(parseInt(new_tech_id))
                            console.log(new_employee_array)
                            event.setExtendedProp('contractors', new_employee_array)
                        }
                        calendar.refetchEvents();
                    }
                }
            });
        }
    }


        let calendarEl = document.getElementById('calendar');

        let droppedElID = 0
        let droppedElScheduleID = 0


        document.addEventListener('DOMContentLoaded', function() {
            calendar = new FullCalendar.Calendar(calendarEl, {
                editable: false,
                allDaySlot: false,
                businessHours: {
                  daysOfWeek: [ 1, 2, 3, 4, 5 ],
                  startTime: '07:00',
                  endTime: '15:00',
                },
                initialView: 'timeGridWeek',
                timeZone: 'local',
                events: function (timezone, callback) {
                    $.ajax({
                        url: '/tech/get_schedule_list',
                        success: function (data) {
                            myEvents = []
                            calendar.removeAllEvents();
                            data.forEach(function (order) {
                                if (order.maintenance_id) {
                                    myEvents.push({
                                        title: order.title,
                                        start: order.start,
                                        end: order.end,
                                        id: 'maintenance-' + order.maintenance_id,
                                        backgroundColor: order.bg_color,
                                        borderColor: order.bg_color,
                                        textColor: order.color,
                                        extendedProps: {
                                            'project_number': order.project_number,
                                            'project_name': order.project_name,
                                            'project_address': order.location,
                                            'customer_name': order.customer,
                                            'mep': order.engineer,
                                            'predemo': order.predemo,
                                            'poc_name': order.poc_name,
                                            'poc_cell_phone': order.poc_cell_phone,
                                            'poc_office_phone': order.poc_office_phone,
                                            'control_system': (order.control_system === 'None' ? '' : order.control_system),
                                            'special_instruction': order.special_instruction,
                                            'tech_note': order.tech_note,
                                            'price': order.price,
                                            'equipment_submittals_link': order.equipment_submittals_link,
                                            'test_sheets_link': order.test_sheets_link,
                                            'tech_marked_drawing_link': order.tech_marked_drawing_link,
                                            'site_pictures_link': order.site_pictures_link,
                                            'cs_software_link': order.cs_software_link,
                                            'estimate': order.estimate,
                                            'employees': order.assigned_to_employees,
                                            'employees_names': order.assigned_to_employees_names,
                                            'contractors': order.assigned_to_contractors,
                                            'contractors_names': order.assigned_to_contractors_names,
                                            'order_id': order.order_id,
                                            'maintenance_id': order.maintenance_id,
                                            'completed': order.completed,
                                            'test_sheet_id': order.test_sheet_id,
                                        }
                                    });
                                } else {
                                    myEvents.push({
                                        title: order.project_number + '<br />' + order.title,
                                        start: order.start,
                                        end: order.end,
                                        id: 'schedule-' + order.schedule_id,
                                        backgroundColor: ((order.assigned == true) ? '#8950fc' : '#3699ff'),
                                        extendedProps: {
                                            'project_number': order.project_number,
                                            'project_name': order.project_name,
                                            'project_address': order.location,
                                            'customer_name': order.customer,
                                            'mep': order.engineer,
                                            'predemo': order.predemo,
                                            'poc_name': order.poc_name,
                                            'poc_cell_phone': order.poc_cell_phone,
                                            'poc_office_phone': order.poc_office_phone,
                                            'control_system': (order.control_system === 'None' ? '' : order.control_system),
                                            'special_instruction': order.special_instruction,
                                            'tech_note': order.tech_note,
                                            'price': order.price,
                                            'equipment_submittals_link': order.equipment_submittals_link,
                                            'test_sheets_link': order.test_sheets_link,
                                            'tech_marked_drawing_link': order.tech_marked_drawing_link,
                                            'site_pictures_link': order.site_pictures_link,
                                            'cs_software_link': order.cs_software_link,
                                            'estimate': order.estimate,
                                            'employees': order.assigned_to_employees,
                                            'employees_names': order.assigned_to_employees_names,
                                            'contractors': order.assigned_to_contractors,
                                            'contractors_names': order.assigned_to_contractors_names,
                                            'partial': order.partial,
                                            'order_id': order.order_id,
                                            'schedule_id': order.schedule_id,
                                            'assigned': order.assigned,
                                            'test_sheet_id': order.test_sheet_id,
                                        }
                                    });
                                }
                            });
                            callback(myEvents);
                        }
                    });
                },
                eventDidMount: function(data) {
                    if (data.event.extendedProps.schedule_id) {
                        data.event.eventColor = ((data.event.extendedProps.assigned == true) ? '#8950fc' : '#3699ff')
                        data.el.setAttribute("data-orderid", data.event.extendedProps.order_id);
                        data.el.setAttribute("data-scheduleid", data.event.extendedProps.schedule_id);
                    } else {
                        data.event.eventColor = ((data.event.extendedProps.completed == true) ? '#ffc107' : 'rgb(108, 117, 125)')
                        data.el.setAttribute("data-orderid", data.event.extendedProps.order_id);
                        data.el.setAttribute("data-maintenanceid", data.event.extendedProps.maintenance_id);
                    }
                    data.el.setAttribute('ondrop', 'dropTech(event)');
                    data.el.setAttribute('ondragover', 'allowDropTech(event)');
                },
                eventContent: function (arg) {
                    console.log(arg.event)
                    let returnHtml = '<div class="text-left">' + arg.timeText + '<br />' + arg.event.title + '</div>'
                    if (arg.event.extendedProps.employees_names) {
                        arg.event.extendedProps.employees_names.forEach(function (employee) {
                            returnHtml += '<i class="d-block text-left p-1 font-weight-bolder">' + employee + '</i>'
                        })
                    }
                    if (arg.event.extendedProps.contractors_names) {
                        arg.event.extendedProps.contractors_names.forEach(function (contractor) {
                            returnHtml += '<i class="d-block text-left p-1 font-weight-bolder">' + contractor + '</i>'
                        })
                    }

                    return {
                        html: returnHtml
                    }
                },

                eventDrop: function (info) {
                    if (info.event.extendedProps.schedule_id) {
                        $.ajax({
                            type: "POST",
                            url: "/schedule/update_schedule/",
                            data: {
                                'type': 'calendar_update',
                                'org_order_id': info.event.extendedProps.order_id,
                                'schedule_id': info.event.extendedProps.schedule_id,
                                'new_tech_id': 0,
                                'new_date': info.event.startStr,
                                'new_date_end': info.event.endStr,
                            },
                            success: function (response) {
                                console.log(response)
                                if (response.result === false) {
                                    alert(response.err_msg);
                                    info.revert();
                                } else {

                                }
                            }
                        });
                    } else {
                        $.ajax({
                            type: "POST",
                            url: "/schedule/update_maintenance/",
                            data: {
                                'type': 'calendar_update',
                                'org_order_id': info.event.extendedProps.order_id,
                                'maintenance_id': info.event.extendedProps.maintenance_id,
                                'new_tech_id': 0,
                                'new_date': info.event.startStr,
                                'new_date_end': info.event.endStr,
                            },
                            success: function (response) {
                                console.log(response)
                                if (response.result === false) {
                                    alert(response.err_msg);
                                    info.revert();
                                } else {

                                }
                            }
                        });
                    }
                },



                eventClick: function (info) {
                    let schedule_information = ''
                    if (info.event.extendedProps.schedule_id) {
                        $.ajax({
                            url: '/schedule/get_schedule_info/' + info.event.extendedProps.schedule_id + '/',
                            method: 'POST',
                            async: false,
                            success: function (data) {
                                schedule_information = data
                            }
                        });
                        scheduleModal.show();
                        $("#schedule-edit").attr('data-orderid', info.event.extendedProps.order_id);
                        $("#schedule-edit").attr('data-scheduleid', info.event.extendedProps.schedule_id);
                        $("#schedule-edit").removeAttr('data-maintenanceid');
                        $("#schedule-edit #modal-order-id").text(info.event.extendedProps.project_number)
                        $("#schedule-edit .modal-body #project_number").text(info.event.extendedProps.project_number)
                        $("#schedule-edit .modal-body #project_name").text(info.event.extendedProps.project_name)
                        $("#schedule-edit .modal-body #project_address").text(info.event.extendedProps.project_address)
                        $("#schedule-edit .modal-body #customer_name").text(info.event.extendedProps.customer_name)
                        $("#schedule-edit .modal-body #mep_name").text(info.event.extendedProps.mep)
                        $("#schedule-edit .modal-body #pre_demo").html( (parseInt(info.event.extendedProps.predemo) > 0 ? '<i class="fa fa-check text-success fs-3"></i>' : '<i class="fas fa-times text-danger fs-3"></i>') )
                        $("#schedule-edit .modal-body #poc_name").text(info.event.extendedProps.poc_name)
                        $("#schedule-edit .modal-body #poc_phone").text( (info.event.extendedProps.poc_cell_phone != '' ? info.event.extendedProps.poc_cell_phone : '') + ' ' + (info.event.extendedProps.poc_office_phone != '' ? info.event.extendedProps.poc_office_phone : '') )
                        $("#schedule-edit .modal-body #control_system").text(info.event.extendedProps.control_system)
                        $("#schedule-edit .modal-body #special_instruction").text(info.event.extendedProps.special_instruction)
                        $("#schedule-edit .modal-body #tech_note").text(info.event.extendedProps.tech_note)
                        $('#schedule-edit .modal-body #start_date').text(dateFormat(info.event.start, 'mediumDateTime'));
                        $('#schedule-edit .modal-body #end_date').text(dateFormat(info.event.end, 'mediumDateTime'));
                        $('#schedule-edit .modal-body #price').text('$' + info.event.extendedProps.price);

                        let url_mask = '#'
                        if (info.event.extendedProps.test_sheet_id == '') {
                            $('#schedule-edit .modal-body #test_sheet_link').html('The Desired Test Sheet are not Available, Contact Your Supervisor.');
                        }
                        else {
                            url_mask = "/sheetcreator/equipments_list/" + info.event.extendedProps.test_sheet_id;
                            $('#schedule-edit .modal-body #test_sheet_link').html('<a href="' + url_mask +'"><button>Go To Project Air Moving Test Sheet</button></a>');
                        }
                        $('#schedule-edit .modal-body #equipment_submittal').attr('href', ((info.event.extendedProps.equipment_submittals_link != '') ? info.event.extendedProps.equipment_submittals_link: '#'));
                        if (info.event.extendedProps.equipment_submittals_link == '')
                            $('#schedule-edit .modal-body #equipment_submittal button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #equipment_submittal button').prop('disabled', false);
                        $('#schedule-edit .modal-body #test_sheets').attr('href', ((info.event.extendedProps.test_sheets_link != '') ? info.event.extendedProps.test_sheets_link : '#'));
                        if (info.event.extendedProps.test_sheets_link == '')
                            $('#schedule-edit .modal-body #test_sheets button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #test_sheets button').prop('disabled', false);
                        $('#schedule-edit .modal-body #tech_marked_drawing').attr('href', ((info.event.extendedProps.tech_marked_drawing_link != '') ? info.event.extendedProps.tech_marked_drawing_link : '#'));
                        if (info.event.extendedProps.tech_marked_drawing_link == '')
                            $('#schedule-edit .modal-body #tech_marked_drawing button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #tech_marked_drawing button').prop('disabled', false);
                        $('#schedule-edit .modal-body #site_pictures button').attr('href', ((info.event.extendedProps.site_pictures_link != '') ? info.event.extendedProps.site_pictures_link : '#'));
                        if (info.event.extendedProps.site_pictures_link == '')
                            $('#schedule-edit .modal-body #site_pictures button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #site_pictures button').prop('disabled', false);
                        $('#schedule-edit .modal-body #cs_software button').attr('href', ((info.event.extendedProps.cs_software_link != '') ? info.event.extendedProps.cs_software_link : '#'));
                        if (info.event.extendedProps.cs_software_link == '')
                            $('#schedule-edit .modal-body #cs_software button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #cs_software button').prop('disabled', false);
                        $('#schedule-edit .modal-body #employee_list').text('');
                        $('#schedule-edit .modal-body #contractor_list').text('');
                        $('#schedule-edit .modal-body #estimated_total_hours').text((info.event.extendedProps.estimate/60).toFixed(1));
                        for (let tech of schedule_information.techs) {
                            if (tech.tech_type == 'employee') {
                                $('#schedule-edit .modal-body #employee_list').append('<div id="' + tech.tech_id + '" class="an-assigned border rounded d-inline-block px-2 py-0 mx-1 my-1">' + tech.tech_name + '<div class="d-inline-block involvement_percentage mx-2 my-1"><input type="number" class="form-control involvement_percentage_input" value="' + tech.involvement_percentage + '" /></div> <a class="remove-assigned text-danger h5 text-decoration-none" href="">×</a></div>')
                            } else if (tech.tech_type == 'contractor') {
                                $('#schedule-edit .modal-body #contractor_list').append('<div id="' + tech.tech_id + '" class="an-assigned border rounded d-inline-block px-2 py-0 mx-1 my-1">' + tech.tech_name + '<div class="d-inline-block involvement_percentage mx-2 my-1"><input type="number" class="form-control involvement_percentage_input" value="' + tech.involvement_percentage + '" /></div> <a class="remove-assigned text-danger h5 text-decoration-none" href="">×</a></div>')
                            }
                        }

                        $("#schedule-edit #modal-order-id").text(info.event.extendedProps.project_number)
                        // info.el.style.borderColor = 'red';
                    } else {
                        scheduleModal.show();
                        $("#schedule-edit").attr('data-orderid', info.event.extendedProps.order_id);
                        $("#schedule-edit").removeAttr('data-scheduleid');
                        $("#schedule-edit").attr('data-maintenanceid', info.event.extendedProps.maintenance_id);
                        $("#schedule-edit .modal-body #project_number").text(info.event.extendedProps.project_number)
                        $("#schedule-edit .modal-body #project_name").text(info.event.extendedProps.project_name)
                        $("#schedule-edit .modal-body #project_address").text(info.event.extendedProps.project_address)
                        $("#schedule-edit .modal-body #customer_name").text(info.event.extendedProps.customer_name)
                        $("#schedule-edit .modal-body #mep_name").text(info.event.extendedProps.mep)
                        $("#schedule-edit .modal-body #pre_demo").html( (parseInt(info.event.extendedProps.predemo) > 0 ? '<i class="fa fa-check text-success fs-3"></i>' : '<i class="fas fa-times text-danger fs-3"></i>') )
                        $("#schedule-edit .modal-body #poc_name").text(info.event.extendedProps.poc_name)
                        $("#schedule-edit .modal-body #poc_phone").text( (info.event.extendedProps.poc_cell_phone != '' ? info.event.extendedProps.poc_cell_phone : '') + ' ' + (info.event.extendedProps.poc_office_phone != '' ? info.event.extendedProps.poc_office_phone : '') )
                        $("#schedule-edit .modal-body #control_system").text(info.event.extendedProps.control_system)
                        $("#schedule-edit .modal-body #special_instruction").text(info.event.extendedProps.special_instruction)
                        $("#schedule-edit .modal-body #tech_note").text(info.event.extendedProps.tech_note)
                        $('#schedule-edit .modal-body #start_date').text(dateFormat(info.event.start, 'mediumDateTime'));
                        $('#schedule-edit .modal-body #end_date').text(dateFormat(info.event.end, 'mediumDateTime'));
                        $('#schedule-edit .modal-body #price').text('$' + info.event.extendedProps.price);
                        $('#schedule-edit .modal-body #equipment_submittal').attr('href', info.event.extendedProps.equipment_submittals_link);
                        let url_mask = ''
                        if (info.event.extendedProps.test_sheet_id == '') {
                            $('#schedule-edit .modal-body #test_sheet_link').html('The Desired Test Sheet are not Available, Contact Your Supervisor.');
                        }
                        else {
                            url_mask = "/sheetcreator/equipments_list/" + info.event.extendedProps.test_sheet_id;
                            $('#schedule-edit .modal-body #test_sheet_link').html('<a target="_blank" href="' + url_mask +'"><button class="btn btn-primary">Go To Project Air Moving Test Sheet</button></a>');
                        }
                        if (info.event.extendedProps.equipment_submittals_link == '')
                            $('#schedule-edit .modal-body #equipment_submittal button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #equipment_submittal button').prop('disabled', false);
                        $('#schedule-edit .modal-body #test_sheets').attr('href', info.event.extendedProps.test_sheets_link);
                        if (info.event.extendedProps.test_sheets_link == '')
                            $('#schedule-edit .modal-body #test_sheets button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #test_sheets button').prop('disabled', false);
                        $('#schedule-edit .modal-body #tech_marked_drawing').attr('href', info.event.extendedProps.tech_marked_drawing_link);
                        if (info.event.extendedProps.tech_marked_drawing_link == '')
                            $('#schedule-edit .modal-body #tech_marked_drawing button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #tech_marked_drawing button').prop('disabled', false);
                        $('#schedule-edit .modal-body #site_pictures button').attr('href', info.event.extendedProps.site_pictures_link);
                        if (info.event.extendedProps.site_pictures_link == '')
                            $('#schedule-edit .modal-body #site_pictures button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #site_pictures button').prop('disabled', false);
                        $('#schedule-edit .modal-body #cs_software button').attr('href', info.event.extendedProps.cs_software_link);
                        if (info.event.extendedProps.cs_software_link == '')
                            $('#schedule-edit .modal-body #cs_software button').prop('disabled', true);
                        else
                            $('#schedule-edit .modal-body #cs_software button').prop('disabled', false);
                        $('#schedule-edit .modal-body #employee_list').text('');
                        $('#schedule-edit .modal-body #contractor_list').text('');

                        $("#schedule-edit #modal-order-id").text(info.event.extendedProps.project_number)
                    }
                },

            });
            calendar.render();
        });
        $('#calendar .fc-event').attr('ondrop', 'dropTech(event)').attr('ondragover', 'allowDropTech(event)');



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



        let Draggable = FullCalendar.Draggable;

        let containerEl = document.getElementById('lnb-calendars');
        let calendarEl = document.getElementById('calendar');

        let droppedElID = 0
        let droppedElScheduleID = 0


        new Draggable(containerEl, {
            itemSelector: '.lnb-calendars-item .draggable',
            eventData: function (eventEl) {
                console.log(eventEl)
                if (eventEl.classList.contains('maintenance')) {
                    return {
                        title: 'Maintenance',
                        duration: { minutes: 60 }
                    };
                } else {
                    let minute_duration = eventEl.dataset.estimate
                    if (eventEl.dataset.estimate<60)
                        minute_duration = 60
                    return {
                        title: eventEl.innerText,
                        duration: { minutes: minute_duration },
                    };
                }
            }
        });

        document.addEventListener('DOMContentLoaded', function() {
            calendar = new FullCalendar.Calendar(calendarEl, {
                editable: true,
                allDaySlot: false,
                businessHours: {
                  daysOfWeek: [ 1, 2, 3, 4, 5 ],
                  startTime: '07:00',
                  endTime: '15:00',
                },
                droppable: true,
                initialView: 'timeGridWeek',
                timeZone: 'local',


                events: function (timezone, callback) {
                    $.ajax({
                        url: '/schedule/get_schedule_list/1',
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
                                            'employees': order.assigned_to_employees,
                                            'employees_names': order.assigned_to_employees_names,
                                            'contractors': order.assigned_to_contractors,
                                            'contractors_names': order.assigned_to_contractors_names,
                                            'order_id': order.order_id,
                                            'maintenance_id': order.maintenance_id,
                                            'completed': order.completed
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
                                            'estimate': order.estimate,
                                            'employees': order.assigned_to_employees,
                                            'employees_names': order.assigned_to_employees_names,
                                            'contractors': order.assigned_to_contractors,
                                            'contractors_names': order.assigned_to_contractors_names,
                                            'partial': order.partial,
                                            'order_id': order.order_id,
                                            'schedule_id': order.schedule_id,
                                            'assigned': order.assigned,
                                            'is_predemo': order.is_predemo
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
                    let returnHtml = '<div class="text-left">' + arg.timeText + '<br />' + arg.event.title + '</div>'
                    if (arg.event.extendedProps.is_predemo) {
                        returnHtml += '(predemo)<br />'
                    }
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



                drop: function (info) {
                    const now = new Date();
                    let r = true
                    if (info.draggedEl.attributes['data-id']) {
                        const id = info.draggedEl.dataset.id;
                        const has_pre_demo = info.draggedEl.dataset.predemo;
                        // const estimate = info.draggedEl.dataset.estimate;
                        // let remaining_estimate = estimate;
                        let start = info.date;
                        start = start.setHours(7, 0, 0, 0);
                        if (now>new Date(start)) {
                            r = confirm("This date is before now. Are you sure about it?");
                        }
                        if (r === true) {
                            droppedElID = info.draggedEl.attributes['data-id'].value;
                            info.draggedEl.style.backgroundColor = '#8950fc';
                            // while (remaining_estimate > 480) {
                            //     while (new Date(start).getDay() === 0 || new Date(start).getDay() === 6) {
                            //         start = moment(start).add(1, 'days')
                            //     }
                            //     let end = new moment(start);
                            //     end = end.add(480, 'minutes');
                            //     $.ajax({
                            //         type: "POST",
                            //         url: "/schedule/create_schedule/",
                            //         async: false,
                            //         data: {
                            //             'order_id': id,
                            //             'schedule_start': dateFormat(start, 'isoDateTime'),
                            //             'schedule_end': dateFormat(end, 'isoDateTime')
                            //         },
                            //         success: function (result) {
                            //             droppedElScheduleID = result.schedule_id;
                            //         }
                            //     });
                            //     remaining_estimate = remaining_estimate - 480
                            //     start = moment(start).add(1, 'days')
                            // }
                            // let end = new moment(start);
                            // if (remaining_estimate === estimate) {
                            //     end = end.add(480, 'minutes');
                            // } else {
                            //     while (new Date(start).getDay() === 0 || new Date(start).getDay() === 6) {
                            //         start = moment(start).add(1, 'days')
                            //         end = new moment(start);
                            //     }
                            //     if (remaining_estimate <= 60) {
                            //         end = end.add(60, 'minutes');
                            //     } else {
                            //         end = end.add(remaining_estimate, 'minutes');
                            //         end = end.set({minute:0, second:0, millisecond:0})
                            //     }
                            //
                            // }
                            while (new Date(start).getDay() === 0 || new Date(start).getDay() === 6) {
                                start = moment(start).add(1, 'days')
                            }
                            let end = new moment(start);
                            end = end.add(480, 'minutes');
                            $.ajax({
                                type: "POST",
                                url: "/schedule/create_schedule/",
                                async: false,
                                data: {
                                    'order_id': id,
                                    'schedule_start': dateFormat(start, 'isoDateTime'),
                                    'schedule_end': dateFormat(end, 'isoDateTime'),
                                    'is_predemo': has_pre_demo
                                },
                                success: function (result) {
                                    droppedElScheduleID = result.schedule_id;
                                }
                            });
                        }
                        calendar.refetchEvents();
                    } else {
                        let start = info.date;
                        if (now>new Date(start)) {
                            r = confirm("This date is before now. Are you sure about it?");
                        }
                        if (r === true) {
                            let end = new moment(start);
                            end = end.add(60, 'minutes');
                            $.ajax({
                                type: "POST",
                                url: "/schedule/create_schedule/",
                                async: false,
                                data: {
                                    'maintenance': true,
                                    'schedule_start': dateFormat(start, 'isoDateTime'),
                                    'schedule_end': dateFormat(end, 'isoDateTime')
                                },
                                success: function (result) {
                                }
                            });
                        }
                        calendar.refetchEvents();
                    }
                },

                eventDragStart: function (info) {
                    $('#calendar .fc-timeGridWeek-view .fc-scrollgrid .move-action').addClass('active')
                },

                eventDragStop: function (info) {
                    $('#calendar .fc-timeGridWeek-view .fc-scrollgrid .move-action').removeClass('active')
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

                eventResize: function (info) {
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
                        $("#schedule-edit").modal();
                        $("#schedule-edit").attr('data-orderid', info.event.extendedProps.order_id);
                        $("#schedule-edit").attr('data-scheduleid', info.event.extendedProps.schedule_id);
                        $("#schedule-edit #modal-order-id").text(info.event.extendedProps.project_number)
                        $('#schedule-edit .modal-body #project_name').html(info.event.title);
                        $('#schedule-edit .modal-body #start_date').text(dateFormat(info.event.start, 'mediumDateTime'));
                        $('#schedule-edit .modal-body #end_date').text(dateFormat(info.event.end, 'mediumDateTime'));
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
                        $.ajax({
                            url: '/schedule/get_maintenance_info/' + info.event.extendedProps.maintenance_id + '/',
                            method: 'POST',
                            async: false,
                            success: function (data) {
                                schedule_information = data
                            }
                        });
                        $("#maintenance-edit").modal();
                        $("#maintenance-edit").attr('data-orderid', info.event.extendedProps.order_id);
                        $("#maintenance-edit").attr('data-maintenanceid', info.event.extendedProps.maintenance_id);
                        $("#maintenance-edit #modal-order-id").text(info.event.extendedProps.project_number)
                        $('#maintenance-edit .modal-body #desc').val(schedule_information.desc);
                        $('#maintenance-edit .modal-body #project_name select').val('');
                        if (info.event.extendedProps.order_id)
                            $('#maintenance-edit .modal-body #project_name select').val(info.event.extendedProps.order_id);
                        $('#maintenance-edit .modal-body #start_date').text(dateFormat(info.event.start, 'mediumDateTime'));
                        $('#maintenance-edit .modal-body #end_date').text(dateFormat(info.event.end, 'mediumDateTime'));
                        $('#maintenance-edit .modal-body #employee_list').text('');
                        $('#maintenance-edit .modal-body #contractor_list').text('');
                        $('#maintenance-edit .modal-body #estimated_total_hours').text((info.event.extendedProps.estimate/60).toFixed(1));
                        for (let tech of schedule_information.techs) {
                            if (tech.tech_type == 'employee') {
                                $('#maintenance-edit .modal-body #employee_list').append('<div id="' + tech.tech_id + '" class="an-assigned border rounded d-inline-block px-3 py-2 mx-1 my-1">' + tech.tech_name + ' </div>')
                            } else if (tech.tech_type == 'contractor') {
                                $('#maintenance-edit .modal-body #contractor_list').append('<div id="' + tech.tech_id + '" class="an-assigned border rounded d-inline-block px-3 py-2 mx-1 my-1">' + tech.tech_name + ' </div>')
                            }
                        }

                        $("#maintenance-edit #modal-order-id").text(info.event.extendedProps.project_number)
                    }
                },

            });
            calendar.render();
        });
        $('#calendar .fc-event').attr('ondrop', 'dropTech(event)').attr('ondragover', 'allowDropTech(event)');



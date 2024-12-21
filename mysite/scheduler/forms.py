from django import forms
from django.forms import ModelForm
from django.db.models import Q
from .models import Schedule, User, Order
from django_select2 import forms as s2forms


class ProjectWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "project_number__icontains",
    ]


class ScheduleForm(ModelForm):
    scheduled_for = forms.DateTimeField(widget=forms.DateTimeInput(format='%m/%d/%Y %H:%M'),
                                        input_formats=('%m/%d/%Y %H:%M',))

    class Meta:
        model = Schedule
        fields = [
            'order',
            'schedule_start',
            'schedule_end',
            'created_by',
        ]
        widgets = {
            "order": ProjectWidget,
        }

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

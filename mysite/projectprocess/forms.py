from django.contrib.auth.forms import *
from django.forms import ModelForm
from .models import *


class ProjectProcessForm(ModelForm):

    class Meta:
        model = ProjectProcess
        fields = [
            'order',
            'tech_package',
            'tech_package_date',
            'tech_scheduled',
            'tech_scheduled_date',
            'job_completed',
            'job_completed_date',
            'report_out',
            'report_out_date',
            'invoiced',
            'invoiced_date',
            'completed',
            'completed_date',
        ]

    def __init__(self, *args, **kwargs):
        super(ProjectProcessForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['disabled'] = 'disabled'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
        self.fields['tech_package'].widget.attrs['style'] = 'width: 230px;'
        self.fields['tech_scheduled'].widget.attrs['style'] = 'width: 230px;'
        self.fields['job_completed'].widget.attrs['style'] = 'width: 230px;'
        self.fields['report_out'].widget.attrs['style'] = 'width: 230px;'
        self.fields['invoiced'].widget.attrs['style'] = 'width: 230px;'
        self.fields['completed'].widget.attrs['style'] = 'width: 230px;'


class ProjectProcessPreDemoForm(ModelForm):

    class Meta:
        model = ProjectProcessPreDemo
        fields = [
            'order',
            'tech_package',
            'tech_package_date',
            'tech_scheduled',
            'tech_scheduled_date',
            'job_completed',
            'job_completed_date',
            'report_out',
            'report_out_date',
            'invoiced',
            'invoiced_date',
            'completed',
            'completed_date',
        ]

    def __init__(self, *args, **kwargs):
        super(ProjectProcessPreDemoForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['disabled'] = 'disabled'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
        self.fields['tech_package'].widget.attrs['style'] = 'width: 230px;'
        self.fields['tech_scheduled'].widget.attrs['style'] = 'width: 230px;'
        self.fields['job_completed'].widget.attrs['style'] = 'width: 230px;'
        self.fields['report_out'].widget.attrs['style'] = 'width: 230px;'
        self.fields['invoiced'].widget.attrs['style'] = 'width: 230px;'
        self.fields['completed'].widget.attrs['style'] = 'width: 230px;'

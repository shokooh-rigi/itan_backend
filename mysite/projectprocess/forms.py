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
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

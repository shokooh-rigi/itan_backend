from django.forms import ModelForm
from django import forms
from .models import *


class ReportSheetForm(ModelForm):
    class Meta:
        model = ReportSheet
        fields = [
            'project',
            'report_date',
            'upload_table_of_content',
            'upload_test_sheets',
            'upload_drawing_pdf'
        ]

    def __init__(self, *args, **kwargs):
        super(ReportSheetForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

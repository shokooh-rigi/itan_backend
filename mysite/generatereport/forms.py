from django.forms import ModelForm
from django import forms
from .models import *


class ReportSheetForm(ModelForm):
    class Meta:
        model = ReportSheet
        fields = [
            'project',
            'report_date',
            'general_notes_and_comments',
        ]

    def __init__(self, *args, **kwargs):
        super(ReportSheetForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ReportSheetDrawingForm(ModelForm):
    class Meta:
        model = ReportDrawing
        fields = [
            'report_sheet',
            'drawing_file',
        ]

    def __init__(self, *args, **kwargs):
        super(ReportSheetDrawingForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
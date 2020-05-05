from django import forms
from django.forms import ModelForm

from .models import Report


class ReportForm(ModelForm):
    report_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))

    class Meta:
        model = Report
        fields = [
            'order',
            'report_date',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

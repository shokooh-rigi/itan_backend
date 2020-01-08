from django.forms import ModelForm
from .models import *
from django import forms


class CompanySubmittalViewForm(ModelForm):
    class Meta:
        model = CompanySubmittal
        fields = [
            'customer',
            'project',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(CompanySubmittalViewForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class SubmittalFormsOrdering(ModelForm):
    class Meta:
        model = SubmittalForms
        fields = [
            "submittal",
            "submittal_form",
            "ordering",
        ]

    def __init__(self, *args, **kwargs):
        super(SubmittalFormsOrdering, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

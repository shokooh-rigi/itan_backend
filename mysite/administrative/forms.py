from django import forms
from django.contrib.auth.forms import *
from django.forms import ModelForm
from .models import *


class AdministrativeForm(ModelForm):

    class Meta:
        model = Document
        fields = [
            'type',
            'customer',
            'uploaded_file',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(AdministrativeForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

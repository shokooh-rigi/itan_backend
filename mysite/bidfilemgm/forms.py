from django import forms
from django.contrib.auth.forms import *
from django.forms import ModelForm
from .models import *


class BidFileForm(ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))
    uploaded_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = BidFile
        fields = [
            'customer',
            'project',
            'uploaded_file',
            'due_date',
            'note',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(BidFileForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Person.objects.filter(company__company_type__name__iexact='mechanical contractor')
        self.fields['due_date'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['due_date'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class FileFieldForm(forms.Form):
    attachment = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
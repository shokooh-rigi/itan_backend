from django.contrib.auth.forms import *
from django.forms import ModelForm
from django_select2 import forms as s2forms

from .models import *


class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "company__name__icontains",
        "name__icontains"
    ]


class BidFileForm(ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))
    uploaded_file = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))

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
        widgets = {
            'customer': CustomerWidget,
        }

    def __init__(self, *args, **kwargs):
        super(BidFileForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Person.objects.all()
        self.fields['due_date'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['due_date'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        self.fields['due_date'].widget.attrs['autocomplete'] = 'off'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
        self.fields['customer'].widget.attrs['class'] = 'select2'
        self.fields['project'].widget.attrs['class'] = 'select2'


class BidFileEditForm(ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))
    uploaded_file = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))

    class Meta:
        model = BidFile
        fields = [
            'customer',
            'project',
            'due_date',
            'note',
            'created_by',
        ]

        exclude = ('uploaded_file',)

    def __init__(self, *args, **kwargs):
        super(BidFileEditForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Person.objects.all()
        self.fields['due_date'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['due_date'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        self.fields['due_date'].widget.attrs['autocomplete'] = 'off'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

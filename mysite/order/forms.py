from django.contrib.auth.forms import *
from django.forms import ModelForm
from django_select2 import forms as s2forms

from .models import *


class ProposalWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "id",
        "quote__estimate__project__name__icontains"
    ]


class ArchitectWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "company__name__icontains",
    ]


class OrderForm(ModelForm):
    equipment_submittal = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    colored_drawing = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    site_pictures = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    test_sheets = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Order
        fields = [
            'proposal',
            'architect_name',
            'po_number',
            'date_po_received',
            'estimated_date_of_project',
            'final_offset',
            'predemo_offset',
            'control_system',
            'equipment_submittal',
            'colored_drawing',
            'report_colored_drawing',
            'general_notes_and_comments',
            'field_draw',
            'site_pictures',
            'test_sheets',
            'note',
        ]
        widgets = {
            'proposal': ProposalWidget,
            'architect_name': ArchitectWidget,
        }

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['architect_name'].queryset = Person.objects.filter(company__company_type__name__iexact='architect')
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
        self.fields['proposal'].widget.attrs['class'] = 'select2'


class ChangeOrderForm(ModelForm):
    class Meta:
        model = ChangeOrder
        fields = [
            'order',
            'co_number',
            'date',
            'amount',
            'description',
        ]

    def __init__(self, *args, **kwargs):
        super(ChangeOrderForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ControlSystemForm(ModelForm):
    class Meta:
        model = ControlSystem
        fields = [
            'manufacturer',
            'version_number',
            'os',
            'release_date',
            'control_file_url',
            'documentation',
        ]

    def __init__(self, *args, **kwargs):
        super(ControlSystemForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ControlSystemManufacturerForm(ModelForm):
    class Meta:
        model = ControlSystemManufacturer
        fields = [
            'manufacturer_name',
            'contact_name',
            'tel',
            'fax',
            'mail',
            'web',
        ]

    def __init__(self, *args, **kwargs):
        super(ControlSystemManufacturerForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class TechLabelForm(ModelForm):
    class Meta:
        model = TechLabel
        fields = [
            'order',
            'label_model',
            'detailed_drawing',
            'schedule_drawing',
            'mechanical_drawing',
            'tech_test_sheets',
            'point_of_contact_name',
            'point_of_contact_cell_phone',
            'point_of_contact_office_phone',
            'schedule_date',
            'tech_notes',
        ]

    def __init__(self, *args, **kwargs):
        super(TechLabelForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if hasattr(visible.field.widget, 'input_type'):
                if visible.field.widget.input_type != 'checkbox':
                    visible.field.widget.attrs['class'] = 'form-control'
                elif visible.field.widget.input_type == 'checkbox':
                    visible.field.widget.attrs['class'] = 'form-check-input'
            else:
                visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

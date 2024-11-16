from django.contrib.auth.forms import *
from django.forms import ModelForm
from django_select2 import forms as s2forms
from django import forms
from .models import *

class EquipmentDbForm(forms.ModelForm):
    serial_number = forms.CharField(required=False, max_length=100, label='Serial Number')
    fan_data = forms.CharField(required=False, max_length=100, label='Fan Data')

    class Meta:
        model = EquipmentDb
        fields = ['manufacturer', 'model_number', 'serial_number', 'fan_data']

    def __init__(self, *args, **kwargs):
        sheet_equipment = kwargs.pop('sheet_equipment', None)
        super().__init__(*args, **kwargs)
        if sheet_equipment:
            custom_data = sheet_equipment.sheetequipmentcustomdata_set.filter(key__column_title__icontains='serial').first()
            common_data = sheet_equipment.secd_set.filter(key__column_title__icontains='fan').first()
            self.fields['serial_number'].initial = custom_data.value if custom_data else ''
            self.fields['fan_data'].initial = common_data.value if common_data else ''
                  
class DataSheetForm(forms.Form):
    ITEM_CHOICES = [
        ('', '---------'),
        ('option1', 'Air Moving Equipment 1'),
        ('option2', 'V.A.V Box'),
        ('option3', 'Air Terminal'),
        ('option4', 'Chiller'),
        ('option5', 'Pump'),
        ('option6', 'Velocity'),
        ('option7', 'Dalt'),
        ('option8', 'Flow Measuring'),
        ('option9', 'Primary Heat Exchanger'),
        ('option10', 'Air Moving Equipment 2'),
        ('option11', 'V.A.V Box Fan Heat Schedule'),
        ('option12', 'V.A.V Box Temperature Schedule'),
        ('option13', 'V.A.V Box Schedule'),
        ('option14', 'Induction Unit'),
        ('option15', 'Primary Heat Exchanger 2'),
        ('option16', 'Pitot Traverse Summary'),
        ('option17', 'Hot Water Boiler'),
    ]
    selectedItem_project = forms.CharField()
    selectedItem = forms.ChoiceField(choices=ITEM_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    # project_name = forms.CharField(required=False , empty_value=None)
    sheet_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y' , attrs={'type': 'date'}))
    # system = forms.CharField(max_length=50)
    number_of_equipments = forms.IntegerField()
    facilitytype = forms.CharField()


class DataSheetEquipmentForm(forms.Form):
    equipment = forms.CharField()
    count = forms.IntegerField()

class ProposalWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "id",
        "estimate__project__name__icontains"
    ]


class ArchitectWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "company__name__icontains",
    ]


class OrderForm(ModelForm):
    equipment_submittal = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))
    site_pictures = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))
    test_sheets = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))
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


class GeneralNoteForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'general_notes_and_comments',
        ]
        widgets = {
            'general_notes_and_comments': forms.Textarea(attrs={
                'class': 'form-control',  # Bootstrap class for consistent form styling
                'rows': 5,  # Customize this as needed
                'placeholder': 'Enter general notes and comments here...',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super(GeneralNoteForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ChangeOrderForm(ModelForm):
    class Meta:
        model = ChangeOrder
        fields = [
            'order',
            'co_number',
            'confirmed',
            'date',
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

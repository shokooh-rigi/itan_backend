from django.forms import ModelForm
from django import forms
from .models import *


class FlowSheetForm(ModelForm):
    equipment_quantity = forms.IntegerField(required=True, min_value=1, max_value=50)

    class Meta:
        model = DataSheet
        fields = [
            'test_sheet_type',
            'project',
            'sheet_date',
            'system',
            'equipment_quantity',
            'number_of_equipment_groups'
        ]

    def __init__(self, *args, **kwargs):
        super(FlowSheetForm, self).__init__(*args, **kwargs)
        self.fields['test_sheet_type'].required = False
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class FlowSheetEquipmentForm(ModelForm):
    class Meta:
        model = FlowEquipment
        fields = [
            'sheet',
            'br_number',
            'location',
            'unit_number',
            'model_number',
        ]

    def __init__(self, *args, **kwargs):
        super(FlowSheetEquipmentForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

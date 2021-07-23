from django.forms import ModelForm
from django import forms
from .models import *


class ChillerSheetForm(ModelForm):
    equipment_quantity = forms.IntegerField(required=True, min_value=1, max_value=50)

    class Meta:
        model = DataSheet
        fields = [
            'test_sheet_type',
            'project',
            'sheet_date',
            'system',
            'equipment_quantity'
        ]

    def __init__(self, *args, **kwargs):
        super(ChillerSheetForm, self).__init__(*args, **kwargs)
        self.fields['test_sheet_type'].required = False
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ChillerSheetEquipmentForm(ModelForm):
    class Meta:
        model = ChillerEquipment
        fields = [
            'sheet',
            'unit_number',
            'capacity',
            'serial_number',
        ]

    def __init__(self, *args, **kwargs):
        super(ChillerSheetEquipmentForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

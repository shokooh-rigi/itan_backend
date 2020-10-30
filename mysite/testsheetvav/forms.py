from django.forms import ModelForm
from django import forms
from ..sheetcreator.models import *


class VavSheetForm(ModelForm):
    class Meta:
        model = DataSheet
        fields = [
            'test_sheet_type',
            'project',
            'sheet_date',
            'system',
            'number_of_equipment_groups',
        ]

    def __init__(self, *args, **kwargs):
        super(VavSheetForm, self).__init__(*args, **kwargs)
        self.fields['test_sheet_type'].required = False
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class VavSheetEquipmentForm(ModelForm):
    quantity = forms.IntegerField(required=True, min_value=1)

    class Meta:
        model = DataSheetEquipment
        fields = [
            'sheet',
            'equipment_type',
            'quantity',
        ]

    def __init__(self, *args, **kwargs):
        super(VavSheetEquipmentForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

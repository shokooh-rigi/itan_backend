from django.forms import ModelForm

from .models import *


class SheetForm(ModelForm):
    class Meta:
        model = Sheet
        fields = [
            'test_sheet_type',
            'project',
            'sheet_date',
            'system',
        ]

    def __init__(self, *args, **kwargs):
        super(SheetForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class SheetEquipmentForm(ModelForm):
    class Meta:
        model = SheetEquipment
        fields = [
            'sheet',
            'equipment',
            'quantity',
        ]

    def __init__(self, *args, **kwargs):
        super(SheetEquipmentForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

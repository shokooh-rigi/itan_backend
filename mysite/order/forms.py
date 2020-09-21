from django.forms import ModelForm

from .models import *


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = [
            'proposal',
            'architect_name',
            'po_number',
            'date_po_received',
            'estimated_date_of_project',
            'control_system',
            'equipment_submittal',
            'note',
        ]

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
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
            'manufacturer_contact_info',
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
            'manufacturer_name'
        ]

    def __init__(self, *args, **kwargs):
        super(ControlSystemManufacturerForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

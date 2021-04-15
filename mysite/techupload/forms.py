from django.forms import ModelForm

from ..order.models import *


class TechUploadOrderForm(ModelForm):
    class Meta:
        model = Order
        fields = [
            'equipment_submittal',
            'note',
        ]

    def __init__(self, *args, **kwargs):
        super(TechUploadOrderForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class TechUploadTechLabelForm(ModelForm):
    class Meta:
        model = TechLabel
        fields = [
            'point_of_contact_name',
            'point_of_contact_cell_phone',
            'point_of_contact_name',
        ]

    def __init__(self, *args, **kwargs):
        super(TechUploadTechLabelForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class TechUploadControlSystemForm(ModelForm):
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
        super(TechUploadControlSystemForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

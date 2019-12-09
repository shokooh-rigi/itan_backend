from django import forms
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
            'note',
        ]

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

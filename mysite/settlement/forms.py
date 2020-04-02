from django import forms
from .models import Settlement, SettledOrders, Person
from django.forms import ModelForm


class SettlementForm(ModelForm):
    class Meta:
        model = Settlement
        fields = [
            'contractor',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(SettlementForm, self).__init__(*args, **kwargs)
        self.fields['contractor'].queryset = Person.objects.filter(company__company_type__name__iexact='sub contractor')
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class SettledOrderForm(ModelForm):
    class Meta:
        model = SettledOrders
        fields = [
            'settlement',
            'order',
            'settled_value',
        ]

    def __init__(self, *args, **kwargs):
        super(SettledOrderForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
from django.forms import ModelForm
from django_select2 import forms as s2forms

from .models import *


class OrderWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "id",
        "order__estimate__project__name__icontains"
    ]


class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'order',
            'date_started',
            'date_completed',
            'terms',
            'description',
            'percent_of_performance_completed',
            'attention',
            'edited_on',
            'created_by',
        ]
        widgets = {
            'order': OrderWidget,
        }

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
        self.fields['order'].widget.attrs['class'] = 'select2'


class InvoicePaymentForm(ModelForm):
    class Meta:
        model = InvoiceTransaction
        fields = [
            'invoice',
            'amount',
            'payment_date',
            'payment_no',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(InvoicePaymentForm, self).__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs['style'] = 'padding-left: 24px'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class AccountSummaryForm(ModelForm):
    class Meta:
        model = AccountSummary
        fields = [
            'customer',
            'attention',
            'created_by',
        ]
        widgets = {
            'order': OrderWidget,
        }

    def __init__(self, *args, **kwargs):
        super(AccountSummaryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

from django.forms import ModelForm

from .models import *


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
            'total_payment_received_to_date',
            'past_due_amount',
            'attention',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

from django import forms
from .models import Schedule, Person
from django.forms import ModelForm


class ScheduleForm(ModelForm):
    scheduled_for = forms.DateTimeField(widget=forms.DateTimeInput(format='%m/%d/%Y %H:%M'), input_formats=('%m/%d/%Y %H:%M',))

    class Meta:
        model = Schedule
        fields = [
            'order',
            'assigned_to_employee',
            'assigned_to_contractor',
            'scheduled_for',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to_contractor'].queryset = Person.objects.filter(company__company_type__name__iexact='sub contractor')
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
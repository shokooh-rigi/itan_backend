from django.forms import ModelForm

from .models import Coi, Person


class CoiForm(ModelForm):
    class Meta:
        model = Coi
        fields = [
            'contractor',
            'contract_person_name',
            'email',
            'subject',
            'cc'
        ]

    def __init__(self, *args, **kwargs):
        super(CoiForm, self).__init__(*args, **kwargs)
        self.fields['contractor'].queryset = Person.objects.filter(
            company__company_type__name__iexact='mechanical contractor')
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

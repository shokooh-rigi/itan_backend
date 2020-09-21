from django import forms
from django.forms import ModelForm

from .models import *


class EstimateForm(ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))
    drawing_date = forms.DateField(required=False, widget=forms.DateInput(format='%m/%d/%Y'),
                                   input_formats=('%m/%d/%Y',))
    predemo = forms.FloatField(initial=0)

    class Meta:
        model = Estimate
        fields = [
            'bfm',
            'customer',
            'project',
            'engineer',
            'service',
            'note',
            'due_date',
            'drawing_date',
            'predemo',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(EstimateForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Person.objects.filter(
            company__company_type__name__iexact='mechanical contractor')
        self.fields['engineer'].queryset = Person.objects.filter(
            company__company_type__name__iexact='mechanical engineer')
        self.fields['due_date'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['due_date'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        self.fields['drawing_date'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['drawing_date'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class QuoteForm(ModelForm):
    class Meta:
        model = Quote
        fields = [
            'estimate',
            'note',
        ]

    def __init__(self, *args, **kwargs):
        super(QuoteForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ProposalForm(ModelForm):
    class Meta:
        model = Proposal
        fields = [
            'quote',
            'note',
            'validity',
        ]

    def __init__(self, *args, **kwargs):
        super(ProposalForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class CustomerForm(ModelForm):
    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            "tel",
            "fax",
            "mail",
            "web",
            "created_by"
        ]

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = ContactInfo.objects.filter(company_type__name__iexact='mechanical contractor')

        self.fields['tel'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['tel'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['fax'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['fax'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['mail'].widget.attrs['placeholder'] = 'email@example.com'

        self.fields['web'].widget.attrs['placeholder'] = 'example.com'
        self.fields['web'].widget.attrs[
            'pattern'] = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ManufacturerForm(ModelForm):
    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            "tel",
            "fax",
            "mail",
            "web",
            "created_by"
        ]

    def __init__(self, *args, **kwargs):
        super(ManufacturerForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = ContactInfo.objects.filter(company_type__name__iexact='manufacturer')

        self.fields['tel'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['tel'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['fax'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['fax'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['mail'].widget.attrs['placeholder'] = 'email@example.com'

        self.fields['web'].widget.attrs['placeholder'] = 'example.com'
        self.fields['web'].widget.attrs[
            'pattern'] = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class EngineerForm(ModelForm):
    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            "tel",
            "fax",
            "mail",
            "web",
            "created_by"
        ]

    def __init__(self, *args, **kwargs):
        super(EngineerForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = ContactInfo.objects.filter(company_type__name__iexact='mechanical engineer')

        self.fields['tel'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['tel'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['fax'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['fax'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['mail'].widget.attrs['placeholder'] = 'email@example.com'

        self.fields['web'].widget.attrs['placeholder'] = 'example.com'
        self.fields['web'].widget.attrs[
            'pattern'] = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class CompanyCustomerForm(ModelForm):
    class Meta:
        model = ContactInfo
        fields = [
            "name",
            "tel",
            "fax",
            "mail",
            "web",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "zip",
            "company_type",
            "created_by"
        ]

    def __init__(self, *args, **kwargs):
        super(CompanyCustomerForm, self).__init__(*args, **kwargs)

        self.fields['company_type'].queryset = CompanyType.objects.filter(name__iexact='mechanical contractor')

        self.fields['tel'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['tel'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['fax'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['fax'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['mail'].widget.attrs['placeholder'] = 'email@example.com'

        self.fields['web'].widget.attrs['placeholder'] = 'example.com'
        self.fields['web'].widget.attrs[
            'pattern'] = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'

        self.fields['zip'].widget.attrs['placeholder'] = 'Only numbers allowed'
        self.fields['zip'].widget.attrs['pattern'] = '(\d{5}([\-]\d{4})?)'

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class CompanyEngineerForm(ModelForm):
    class Meta:
        model = ContactInfo
        fields = [
            "name",
            "tel",
            "fax",
            "mail",
            "web",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "zip",
            "company_type",
            "created_by"
        ]

    def __init__(self, *args, **kwargs):
        super(CompanyEngineerForm, self).__init__(*args, **kwargs)

        self.fields['company_type'].queryset = CompanyType.objects.filter(name__iexact='mechanical engineer')

        self.fields['tel'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['tel'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['fax'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['fax'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['mail'].widget.attrs['placeholder'] = 'email@example.com'

        self.fields['web'].widget.attrs['placeholder'] = 'example.com'
        self.fields['web'].widget.attrs[
            'pattern'] = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'

        self.fields['zip'].widget.attrs['placeholder'] = 'Only numbers allowed'
        self.fields['zip'].widget.attrs['pattern'] = '(\d{5}([\-]\d{4})?)'

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "zip",
            "tel",
            "fax",
            "mail",
            "note",
            "created_by"
        ]

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        self.fields['zip'].widget.attrs['placeholder'] = 'Only numbers allowed'
        self.fields['zip'].widget.attrs['pattern'] = '(\d{5}([\-]\d{4})?)'

        self.fields['tel'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['tel'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['fax'].widget.attrs['placeholder'] = 'XXX-XXX-XXXX'
        self.fields['fax'].widget.attrs['pattern'] = '\d{3}[\-]\d{3}[\-]\d{4}'

        self.fields['mail'].widget.attrs['placeholder'] = 'email@example.com'

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class EquipmentForm(ModelForm):
    class Meta:
        model = EstimateEquipment
        fields = [
            "estimate",
            "equipment",
            "quantity",
            "price_override",
        ]

    def __init__(self, *args, **kwargs):
        super(EquipmentForm, self).__init__(*args, **kwargs)
        self.fields['price_override'].widget.attrs['disabled'] = 'disabled'
        self.fields['price_override'].widget.attrs['id'] = 'price_override'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class EstimateDetailsForm(ModelForm):
    class Meta:
        model = EstimateDetails
        fields = [
            "estimate",
            "control_system",
            "hours",
            "pre_demo",
            "adjustment",
            "remark",
            "saved_flag",
        ]

    def __init__(self, *args, **kwargs):
        super(EstimateDetailsForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}

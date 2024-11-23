from django import forms
from django.forms import ModelForm
from django_select2 import forms as s2forms

from .models import *


class EstimateWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "id",
        "project__name__icontains",
    ]


class BFMWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "id",
        "project__name__icontains",
    ]


class ProjectWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
    ]


class CustomerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "company__name__icontains",
    ]


class CustomerFullWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "company__name__icontains",
    ]


class EngineerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "company__name__icontains",
    ]

    def label_from_instance(self, obj):
        return str(obj.company.name)


class EstimateForm(ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(format="%m/%d/%Y"), input_formats=("%m/%d/%Y",)
    )
    drawing_date = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%m/%d/%Y"),
        input_formats=("%m/%d/%Y",),
    )
    predemo = forms.FloatField(initial=0)

    class Meta:
        model = Estimate
        fields = [
            "bfm",
            "customer",
            "project",
            "engineer",
            "service",
            "note",
            "due_date",
            "drawing_date",
            "predemo",
            "created_by",
        ]
        widgets = {
            "bfm": BFMWidget,
            "customer": CustomerWidget,
            "project": ProjectWidget,
            "engineer": EngineerWidget,
        }

    def __init__(self, *args, **kwargs):
        super(EstimateForm, self).__init__(*args, **kwargs)
        self.fields["customer"].queryset = Person.objects.all()
        self.fields["engineer"].queryset = Person.objects.all()
        self.fields["due_date"].widget.attrs["placeholder"] = "mm/dd/YYYY"
        self.fields["due_date"].widget.attrs["pattern"] = "\d{2}[\/]\d{2}[\/]\d{4}"
        self.fields["due_date"].widget.attrs["autocomplete"] = "off"
        self.fields["drawing_date"].widget.attrs["placeholder"] = "mm/dd/YYYY"
        self.fields["drawing_date"].widget.attrs["pattern"] = "\d{2}[\/]\d{2}[\/]\d{4}"
        self.fields["drawing_date"].widget.attrs["autocomplete"] = "off"
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }
        self.fields["bfm"].widget.attrs["class"] = "select2"
        self.fields["customer"].widget.attrs["class"] = "select2"
        self.fields["project"].widget.attrs["class"] = "select2"
        self.fields["engineer"].widget.attrs["class"] = "select2"


class EstimateFullForm(ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(format="%m/%d/%Y"), input_formats=("%m/%d/%Y",)
    )
    drawing_date = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%m/%d/%Y"),
        input_formats=("%m/%d/%Y",),
    )
    predemo = forms.FloatField(initial=0)

    class Meta:
        model = Estimate
        fields = [
            "bfm",
            "customer",
            "project",
            "engineer",
            "service",
            "note",
            "due_date",
            "drawing_date",
            "predemo",
            "created_by",
        ]
        widgets = {
            "bfm": BFMWidget,
            "customer": CustomerFullWidget,
            "project": ProjectWidget,
            "engineer": CustomerWidget,
        }

    def __init__(self, *args, **kwargs):
        super(EstimateFullForm, self).__init__(*args, **kwargs)
        self.fields["customer"].queryset = Person.objects.all()
        self.fields["engineer"].queryset = Person.objects.all()
        self.fields["due_date"].widget.attrs["placeholder"] = "mm/dd/YYYY"
        self.fields["due_date"].widget.attrs["pattern"] = "\d{2}[\/]\d{2}[\/]\d{4}"
        self.fields["due_date"].widget.attrs["autocomplete"] = "off"
        self.fields["drawing_date"].widget.attrs["placeholder"] = "mm/dd/YYYY"
        self.fields["drawing_date"].widget.attrs["pattern"] = "\d{2}[\/]\d{2}[\/]\d{4}"
        self.fields["drawing_date"].widget.attrs["autocomplete"] = "off"
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }
        self.fields["bfm"].widget.attrs["class"] = "select2"
        self.fields["customer"].widget.attrs["class"] = "select2"
        self.fields["project"].widget.attrs["class"] = "select2"
        self.fields["engineer"].widget.attrs["class"] = "select2"


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ["name", "address", "contact_info", "note", "created_by"]

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        # self.fields['name'].widget.attrs['pattern'] = '[^/:?,]+'

        self.fields["zip"].widget.attrs["placeholder"] = "Only numbers allowed"
        self.fields["zip"].widget.attrs["pattern"] = "(\d{5}([\-]\d{4})?)"

        self.fields["tel"].widget.attrs["placeholder"] = "XXX-XXX-XXXX"
        self.fields["tel"].widget.attrs["pattern"] = "\d{3}[\-]\d{3}[\-]\d{4}"

        self.fields["fax"].widget.attrs["placeholder"] = "XXX-XXX-XXXX"
        self.fields["fax"].widget.attrs["pattern"] = "\d{3}[\-]\d{3}[\-]\d{4}"

        self.fields["mail"].widget.attrs["placeholder"] = "email@example.com"

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


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
        self.fields["price_override"].widget.attrs["disabled"] = "disabled"
        self.fields["price_override"].widget.attrs["id"] = "price_override"
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


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
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }

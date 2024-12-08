from django.forms import CharField, ModelForm

from mysite.dbmanagement.models import EquipmentDb, EquipmentManufacturer


class EquipmentDbForm(ModelForm):
    serial_number = CharField(required=False, max_length=100, label="Serial Number")
    fan_data = CharField(required=False, max_length=100, label="Fan Data")

    class Meta:
        model = EquipmentDb
        fields = ["manufacturer", "model_number", "serial_number", "fan_data"]

    def __init__(self, *args, **kwargs):
        sheet_equipment = kwargs.pop("sheet_equipment", None)
        super().__init__(*args, **kwargs)
        if sheet_equipment:
            custom_data = sheet_equipment.sheetequipmentcustomdata_set.filter(
                key__column_title__icontains="serial"
            ).first()
            common_data = sheet_equipment.secd_set.filter(
                key__column_title__icontains="fan"
            ).first()
            self.fields["serial_number"].initial = (
                custom_data.value if custom_data else ""
            )
            self.fields["fan_data"].initial = common_data.value if common_data else ""


class EquipmentForm(ModelForm):
    class Meta:
        model = EquipmentDb
        fields = [
            "equipment_type",
            "manufacturer",
            "model_number",
            "equipment_submittal",
            "image",
        ]

    def __init__(self, *args, **kwargs):
        super(EquipmentForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


class ManufacturerForm(ModelForm):
    class Meta:
        model = EquipmentManufacturer
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
        ]

    def __init__(self, *args, **kwargs):
        super(ManufacturerForm, self).__init__(*args, **kwargs)

        self.fields["tel"].widget.attrs["placeholder"] = "XXX-XXX-XXXX"
        self.fields["tel"].widget.attrs["pattern"] = "\d{3}[\-]\d{3}[\-]\d{4}"

        self.fields["fax"].widget.attrs["placeholder"] = "XXX-XXX-XXXX"
        self.fields["fax"].widget.attrs["pattern"] = "\d{3}[\-]\d{3}[\-]\d{4}"

        self.fields["mail"].widget.attrs["placeholder"] = "email@example.com"

        self.fields["web"].widget.attrs["placeholder"] = "example.com"
        self.fields["web"].widget.attrs[
            "pattern"
        ] = "^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"

        self.fields["zip"].widget.attrs["placeholder"] = "Only numbers allowed"
        self.fields["zip"].widget.attrs["pattern"] = "(\d{5}([\-]\d{4})?)"

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }

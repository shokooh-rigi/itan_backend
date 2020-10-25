from django.contrib import admin
from django import forms
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *


class ManufacturerResource(resources.ModelResource):
    class Meta:
        model = EquipmentManufacturer


class ManufacturerAdmin(ImportExportModelAdmin):
    resource_class = ManufacturerResource


admin.site.register(EquipmentManufacturer, ManufacturerAdmin)


class EqCustomFieldAdmin(admin.TabularInline):
    model = EquipmentCustomField


class EquipmentDbAdmin(admin.ModelAdmin):
    inlines = [EqCustomFieldAdmin, ]


admin.site.register(EquipmentDb, EquipmentDbAdmin)


class SupplierAdminForm(forms.ModelForm):
    class Meta:
        model = EquipmentTypeCustomOperation
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(SupplierAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['result_field'].queryset = EquipmentTypeCustomField.objects.filter(equipment_type=61)


class EqTypeCustomFieldAdmin(admin.TabularInline):
    model = EquipmentTypeCustomField


class EqTypeCustomOperationAdmin(admin.TabularInline):
    model = EquipmentTypeCustomOperation


class ActualDataCustomOperationAdmin(admin.TabularInline):
    model = ActualDataCustomOperation


class EquipmentTypeAdmin(admin.ModelAdmin):
    inlines = [EqTypeCustomFieldAdmin, EqTypeCustomOperationAdmin, ActualDataCustomOperationAdmin, ]


admin.site.register(Equipment, EquipmentTypeAdmin)


class TestSheetFieldAdmin(admin.TabularInline):
    model = TestSheetField


class TestSheetOperationAdmin(admin.TabularInline):
    model = TestSheetOperation


class TestSheetAdmin(admin.ModelAdmin):
    inlines = [TestSheetFieldAdmin, TestSheetOperationAdmin, ]

    class Media:
        js = (
            '../static/js/jquery-3.5.1.min.js',  # jquery
            '../static/js/admin.js',  # project static folder
        )


admin.site.register(TestSheet, TestSheetAdmin)

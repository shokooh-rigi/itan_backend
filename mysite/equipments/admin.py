from .models import TestSheet, Equipment, DataSheet
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class TestSheetAdmin(admin.ModelAdmin):
    model = TestSheet
    list_display = ('id', 'name', 'created_on')
    search_fields = ('id', 'name')

admin.site.register(TestSheet, TestSheetAdmin)


class EquipmentAdmin(admin.ModelAdmin):
    model = Equipment
    list_display = ('id', 'name', 'service', 'test_sheet', 'price', 'created_on',)
    search_fields = ('id',)

admin.site.register(Equipment, EquipmentAdmin)


class DataSheetAdmin(admin.ModelAdmin):
    model = DataSheet
    list_display = ('id', 'name', 'project', 'equipment_type', 'manufacturer', 'model_number',)
    search_fields = ('id',  'name',)

admin.site.register(DataSheet, DataSheetAdmin)

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase

from .models import *

# Register your models here.

admin.site.register(SheetActualDataCustomField)


class DataSheetEquipmentAdmin(SortableInlineAdminMixin, admin.TabularInline):
    model = DataSheetEquipment
    readonly_fields = ('id',)
    exclude = ('equipment_type', 'equipment', 'number_of_supply_air_terminal',
               'number_of_return_air_terminal', 'number_of_outside_air_terminal', 'main_data_entry_completed',
               'design_data_entry_completed', 'actual_data_entry_completed',
               'terminal_design_data_entry_completed', 'terminal_actual_data_entry_completed',)


class DataSheetAdmin(admin.ModelAdmin, SortableAdminBase):
    inlines = [DataSheetEquipmentAdmin, ]


admin.site.register(DataSheet, DataSheetAdmin)


class SheetEquipmentAdmin(SortableInlineAdminMixin, admin.TabularInline):
    model = SheetEquipment
    readonly_fields = ('id',)
    exclude = ('equipment_type', 'equipment', 'number_of_supply_air_terminal',
               'number_of_return_air_terminal', 'number_of_outside_air_terminal', 'main_data_entry_completed',
               'design_data_entry_completed', 'actual_data_entry_completed',
               'terminal_design_data_entry_completed', 'terminal_actual_data_entry_completed',)


class SheetAdmin(admin.ModelAdmin, SortableAdminBase):
    inlines = [SheetEquipmentAdmin, ]


admin.site.register(Sheet, SheetAdmin)

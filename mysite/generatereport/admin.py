from django.contrib import admin

from mysite.generatereport.models import DataSheet

# Register your models here.


class DataSheetAdmin(admin.ModelAdmin):
    model = DataSheet
    list_display = ('id', 'name', 'project', 'equipment_type', 'manufacturer', 'model_number',)
    search_fields = ('id',  'name',)

admin.site.register(DataSheet, DataSheetAdmin)

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *

# Register your models here.


class BidFileResource(resources.ModelResource):
    class Meta:
        model = BidFile


class BidFileAdmin(ImportExportModelAdmin):
    resource_class = BidFileResource


admin.site.register(BidFile, BidFileAdmin)


class EquipmentSubmittalResource(resources.ModelResource):
    class Meta:
        model = EquipmentSubmittal


class EquipmentSubmittalAdmin(ImportExportModelAdmin):
    resource_class = EquipmentSubmittalResource


admin.site.register(EquipmentSubmittal, EquipmentSubmittalAdmin)

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *


class BidResource(resources.ModelResource):
    class Meta:
        model = Bid


class BidAdmin(ImportExportModelAdmin):
    resource_class = BidResource
    search_fields = ('project__name',)


admin.site.register(Bid, BidAdmin)


class EquipmentSubmittalResource(resources.ModelResource):
    class Meta:
        model = EquipmentSubmittal


class EquipmentSubmittalAdmin(ImportExportModelAdmin):
    resource_class = EquipmentSubmittalResource


admin.site.register(EquipmentSubmittal, EquipmentSubmittalAdmin)

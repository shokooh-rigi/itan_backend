from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from mysite.bidfilemgm.models import BidFile, EquipmentSubmittal, BidAttachment


class BidFileResource(resources.ModelResource):
    class Meta:
        model = BidFile


class BidFileAdmin(ImportExportModelAdmin):
    resource_class = BidFileResource
    search_fields = ('project__name',)


admin.site.register(BidFile, BidFileAdmin)


class EquipmentSubmittalResource(resources.ModelResource):
    class Meta:
        model = EquipmentSubmittal


class EquipmentSubmittalAdmin(ImportExportModelAdmin):
    resource_class = EquipmentSubmittalResource


admin.site.register(EquipmentSubmittal, EquipmentSubmittalAdmin)


class BidAttachmentResource(resources.ModelResource):
    """
    Resource configuration for importing/exporting BidAttachment model data.
    """
    class Meta:
        model = BidAttachment


@admin.register(BidAttachment)
class BidAttachmentAdmin(ImportExportModelAdmin):
    """
    Admin configuration for BidAttachment model with import/export functionality.
    """
    resource_class = BidAttachmentResource
    list_display = ('id', 'bid', 'uploaded_file', 'created_by', 'created_on')
    list_filter = ('created_on',)
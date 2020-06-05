from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import TypesOfDocument, Document


class TypesOfDocumentResource(resources.ModelResource):
    class Meta:
        model = TypesOfDocument


class TypesOfDocumentAdmin(ImportExportModelAdmin):
    resource_class = TypesOfDocumentResource


admin.site.register(TypesOfDocument, TypesOfDocumentAdmin)


class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document


class DocumentAdmin(ImportExportModelAdmin):
    resource_class = DocumentResource


admin.site.register(Document, DocumentAdmin)

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Coi, InsuranceCompany


# Register your models here.


class InsuranceCompanyAdmin(ImportExportModelAdmin):
    readonly_fields = (
        'key',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(InsuranceCompany, InsuranceCompanyAdmin)


class CoiAdmin(ImportExportModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Coi, CoiAdmin)

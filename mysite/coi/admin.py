from django.contrib import admin
from .models import Coi, InsuranceCompany

# Register your models here.


class InsuranceCompanyAdmin(admin.ModelAdmin):

    readonly_fields = (
        'key',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(InsuranceCompany, InsuranceCompanyAdmin)


class CoiAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Coi, CoiAdmin)

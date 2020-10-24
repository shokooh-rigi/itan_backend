from __future__ import unicode_literals
from django import forms
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from mysite.core.models import *

admin.site.register(CompanySubmittalForm)
admin.site.register(EmailBodyTemplate)
admin.site.register(ModulesToEmailTemplateRelation)


class LogEntryAdmin(admin.ModelAdmin):
    readonly_fields = ('content_type',
                       'user',
                       'action_time',
                       'object_id',
                       'object_repr',
                       'action_flag',
                       'change_message'
                       )

    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(LogEntry, LogEntryAdmin)


class LicenseInfoAdmin(ImportExportModelAdmin):

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(LicenseInfo, LicenseInfoAdmin)


class LicenseFilesAdmin(ImportExportModelAdmin):

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(LicenseFiles, LicenseFilesAdmin)


class SettingAdmin(ImportExportModelAdmin):
    readonly_fields = ('key',
                       )

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Setting, SettingAdmin)


class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service


class ServiceAdmin(ImportExportModelAdmin):
    resource_class = ServiceResource


admin.site.register(Service, ServiceAdmin)


class CompanyTypeResource(resources.ModelResource):
    class Meta:
        model = CompanyType


class CompanyTypeAdmin(ImportExportModelAdmin):
    resource_class = CompanyTypeResource


admin.site.register(CompanyType, CompanyTypeAdmin)


class ContactInfoAdmin(ImportExportModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(ContactInfo, ContactInfoAdmin)


class PersonAdmin(ImportExportModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(Person, PersonAdmin)


class ProfileResource(resources.ModelResource):
    class Meta:
        model = Profile


class ProfileAdmin(ImportExportModelAdmin):
    resource_class = ProfileResource


admin.site.register(Profile, ProfileAdmin)


class ProjectAdmin(ImportExportModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(Project, ProjectAdmin)

admin.site.register(CreditCard)
admin.site.register(BusinessCheckingAccount)
admin.site.register(TechLabelModel)

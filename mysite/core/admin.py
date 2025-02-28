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


class AutoAssignCreatedByAdmin(ImportExportModelAdmin):
    """Automatically assigns `created_by` to the logged-in user on object creation."""

    def get_exclude(self, request, obj=None):
        """Dynamically exclude `created_by` if it exists in the model."""
        exclude_fields = super().get_exclude(request, obj) or []
        if hasattr(self.model, "created_by"):
            exclude_fields = list(exclude_fields) + ["created_by"]
        return exclude_fields

    def save_model(self, request, obj, form, change):
        if not obj.pk and hasattr(obj, "created_by"):  # Check if field exists
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class LogEntryAdmin(admin.ModelAdmin):
    readonly_fields = (
        "content_type",
        "user",
        "action_time",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )

    list_filter = ["user", "content_type", "action_flag"]

    search_fields = ["object_repr", "change_message"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(LogEntry, LogEntryAdmin)


class LicenseInfoAdmin(AutoAssignCreatedByAdmin):

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(LicenseInfo, LicenseInfoAdmin)


class LicenseFilesAdmin(AutoAssignCreatedByAdmin):

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(LicenseFiles, LicenseFilesAdmin)


class SettingAdmin(AutoAssignCreatedByAdmin):
    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Setting, SettingAdmin)


class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service


class ServiceAdmin(AutoAssignCreatedByAdmin):
    resource_class = ServiceResource


admin.site.register(Service, ServiceAdmin)


class CompanyTypeResource(resources.ModelResource):
    class Meta:
        model = CompanyType


class CompanyTypeAdmin(AutoAssignCreatedByAdmin):
    resource_class = CompanyTypeResource


admin.site.register(CompanyType, CompanyTypeAdmin)


class ContactInfoAdmin(AutoAssignCreatedByAdmin):
    search_fields = [
        "tel",
        "cel",
        "fax",
        "mail",
        "web",
    ]
    readonly_fields = (
        "created_by",
        "created_on",
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(ContactInfo, ContactInfoAdmin)


class PersonAdmin(AutoAssignCreatedByAdmin):
    search_fields = ["company__name", "name"]
    readonly_fields = (
        "created_by",
        "created_on",
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(Person, PersonAdmin)


class ProfileResource(resources.ModelResource):
    class Meta:
        model = Profile


class ProfileAdmin(AutoAssignCreatedByAdmin):
    resource_class = ProfileResource


admin.site.register(Profile, ProfileAdmin)


class ProjectAdmin(AutoAssignCreatedByAdmin):
    readonly_fields = (
        "created_by",
        "created_on",
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(Project, ProjectAdmin)


class CreditCardAdmin(AutoAssignCreatedByAdmin):
    pass


class BusinessCheckingAccountAdmin(AutoAssignCreatedByAdmin):
    pass


class TechLabelModelAdmin(AutoAssignCreatedByAdmin):
    pass


class AnnouncementAdmin(AutoAssignCreatedByAdmin):
    pass


# Register them
admin.site.register(CreditCard, CreditCardAdmin)
admin.site.register(BusinessCheckingAccount, BusinessCheckingAccountAdmin)
admin.site.register(TechLabelModel, TechLabelModelAdmin)
admin.site.register(Announcement, AnnouncementAdmin)

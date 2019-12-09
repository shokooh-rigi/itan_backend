from __future__ import unicode_literals
from django.contrib import admin
from django.contrib.admin.models import LogEntry

from .models import *

admin.site.register(Profile)
admin.site.register(Equipment)
admin.site.register(TestSheet)


class PersonAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(Person, PersonAdmin)


class ContactInfoAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(ContactInfo, ContactInfoAdmin)


class ProjectAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(Project, ProjectAdmin)
admin.site.register(CompanyType)
admin.site.register(Service)
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


class LicenseInfoAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(LicenseInfo, LicenseInfoAdmin)


class LicenseFilesAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(LicenseFiles, LicenseFilesAdmin)


class SettingAdmin(admin.ModelAdmin):
    readonly_fields = ('key',
                       )

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Setting, SettingAdmin)

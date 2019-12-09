from django.contrib import admin
from .models import *


class SubmittalAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.save()


admin.site.register(CompanySubmittal, SubmittalAdmin)

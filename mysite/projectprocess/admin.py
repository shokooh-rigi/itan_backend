from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *
# Register your models here.


class ProjectProcessResource(resources.ModelResource):
    class Meta:
        model = ProjectProcess


class ProjectProcessAdmin(ImportExportModelAdmin):
    resource_class = ProjectProcessResource


admin.site.register(ProjectProcess, ProjectProcessAdmin)


class ProjectProcessPreDemoResource(resources.ModelResource):
    class Meta:
        model = ProjectProcessPreDemo


class ProjectProcessPreDemoAdmin(ImportExportModelAdmin):
    resource_class = ProjectProcessPreDemoResource


admin.site.register(ProjectProcessPreDemo, ProjectProcessPreDemoAdmin)

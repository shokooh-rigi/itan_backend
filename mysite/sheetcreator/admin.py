from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *

# Register your models here.

admin.site.register(Sheet)
admin.site.register(SheetActualDataCustomField)

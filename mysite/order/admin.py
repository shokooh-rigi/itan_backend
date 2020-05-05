from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *


# Register your models here.


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order


class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource


admin.site.register(Order, OrderAdmin)

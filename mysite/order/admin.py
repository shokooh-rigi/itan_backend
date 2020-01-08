from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# Register your models here.


class OrderResource(resources.ModelResource):

    class Meta:
        model = Order


class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource


admin.site.register(Order, OrderAdmin)

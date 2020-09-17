from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from ajax_select.admin import AjaxSelectAdmin
from ajax_select import make_ajax_form

from .models import *


# Register your models here.


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order


class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource


admin.site.register(Order, OrderAdmin)


@admin.register(ControlSystem)
class ControlSystemAdmin(AjaxSelectAdmin):

    form = make_ajax_form(ControlSystem, {
        # fieldname: channel_name
        'manufacturer': 'controlsystem'
    })


class ControlSystemManufacturerResource(resources.ModelResource):
    class Meta:
        model = ControlSystemManufacturer


class ControlSystemManufacturerAdmin(ImportExportModelAdmin):
    resource_class = ControlSystemManufacturerResource


admin.site.register(ControlSystemManufacturer, ControlSystemManufacturerAdmin)

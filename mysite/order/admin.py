from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from mysite.order.models import Order, ControlSystem, ControlSystemManufacturer, TechLabel, ChangeOrder


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order


# class OrderAdmin(ImportExportModelAdmin):
class OrderAdmin(admin.ModelAdmin):
    # resource_class = OrderResource
    search_fields = ['project_number']
    fieldsets = [
        ('Order Information', {'fields': ['project_number', 'colored_drawing', 'report_colored_drawing']}),
    ]


admin.site.register(Order, OrderAdmin)


class ControlSystemResource(resources.ModelResource):
    class Meta:
        model = ControlSystem


class ControlSystemAdmin(ImportExportModelAdmin):
    resource_class = ControlSystemResource


admin.site.register(ControlSystem, ControlSystemAdmin)


class ControlSystemManufacturerResource(resources.ModelResource):
    class Meta:
        model = ControlSystemManufacturer


class ControlSystemManufacturerAdmin(ImportExportModelAdmin):
    resource_class = ControlSystemManufacturerResource


admin.site.register(ControlSystemManufacturer, ControlSystemManufacturerAdmin)


class TechLabelResource(resources.ModelResource):
    class Meta:
        model = TechLabel


class TechLabelAdmin(ImportExportModelAdmin):
    resource_class = TechLabelResource


admin.site.register(TechLabel, TechLabelAdmin)
admin.site.register(ChangeOrder)

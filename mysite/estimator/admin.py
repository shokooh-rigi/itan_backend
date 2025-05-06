from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from mysite.estimator.models import EstimateEquipment, Estimate, EstimateDetails, EstimateHistory


class EstimateAdmin(ImportExportModelAdmin):
    readonly_fields = ('created_by', 'created_on',)
    search_fields = ('project__name', 'id')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        for this_equipment in EstimateEquipment.objects.filter(estimate=obj.id):
            if this_equipment.equipment.service not in form.cleaned_data['service']:
                this_equipment.flag = False
        obj.save()


admin.site.register(Estimate, EstimateAdmin)


class EstimateEquipmentResource(resources.ModelResource):
    class Meta:
        model = EstimateEquipment


class EstimateEquipmentAdmin(ImportExportModelAdmin):
    resource_class = EstimateEquipmentResource
    list_display = ('id', 'estimate', 'equipment')


admin.site.register(EstimateEquipment, EstimateEquipmentAdmin)


class EstimateDetailsResource(resources.ModelResource):
    class Meta:
        model = EstimateDetails


class EstimateDetailsAdmin(ImportExportModelAdmin):
    resource_class = EstimateDetailsResource


admin.site.register(EstimateDetails, EstimateDetailsAdmin)


class EstimateHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'estimate',
        'total',
        'version',
        'created_on',
        'updated_at'
    )
    list_filter = ('estimate', 'created_on')
    search_fields = ('estimate__id', 'version')
    ordering = ('-created_on',)
    readonly_fields = ('created_on', 'updated_at')

admin.site.register(EstimateHistory, EstimateHistoryAdmin)
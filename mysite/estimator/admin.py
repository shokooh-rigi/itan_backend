from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources


# Register your models here.


class EstimateAdmin(ImportExportModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        for this_equipment in EstimateEquipment.objects.filter(estimate=obj.id):
            if this_equipment.equipment.service not in form.cleaned_data['service']:
                this_equipment.delete()
        obj.save()


admin.site.register(Estimate, EstimateAdmin)


class QuoteResource(resources.ModelResource):

    class Meta:
        model = Quote


class QuoteAdmin(ImportExportModelAdmin):
    resource_class = QuoteResource


admin.site.register(Quote, QuoteAdmin)


class ProposalResource(resources.ModelResource):

    class Meta:
        model = Proposal


class ProposalAdmin(ImportExportModelAdmin):
    resource_class = ProposalResource


admin.site.register(Proposal, ProposalAdmin)


class EstimateEquipmentResource(resources.ModelResource):

    class Meta:
        model = EstimateEquipment


class EstimateEquipmentAdmin(ImportExportModelAdmin):
    resource_class = EstimateEquipmentResource


admin.site.register(EstimateEquipment, EstimateEquipmentAdmin)


class EstimateDetailsResource(resources.ModelResource):

    class Meta:
        model = EstimateDetails


class EstimateDetailsAdmin(ImportExportModelAdmin):
    resource_class = EstimateDetailsResource


admin.site.register(EstimateDetails, EstimateDetailsAdmin)

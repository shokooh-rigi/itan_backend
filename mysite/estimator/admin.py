from django.contrib import admin
from .models import *

# Register your models here.


class EstimateAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'created_on',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        for this_equipment in EstimateEquipment.objects.filter(estimate=obj.id):
            if this_equipment.equipment.service not in form.cleaned_data['service']:
                this_equipment.delete()
        obj.save()


admin.site.register(Estimate, EstimateAdmin)
admin.site.register(Quote)
admin.site.register(Proposal)
admin.site.register(EstimateEquipment)
admin.site.register(EstimateDetails)

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from mysite.proposal.models import Proposal


class ProposalResource(resources.ModelResource):
    class Meta:
        model = Proposal


class ProposalAdmin(ImportExportModelAdmin):
    resource_class = ProposalResource


admin.site.register(Proposal, ProposalAdmin)


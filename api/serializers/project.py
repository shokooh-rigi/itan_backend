from rest_framework import serializers

from mysite.bidfilemgm.models import BidFile
from mysite.estimator.models import Proposal
from mysite.order.models import Order
from mysite.gi.models import Invoice
from mysite.report.models import Report


def get_project_step(project):
    steps_date = [1, '', '', '', '', '', '', '', '', '']
    steps_date[1] = project.created_on
    if Proposal.objects.filter(quote__estimate__bfm__id=project.id).exists():
        steps_date[0] = 2
        steps_date[2] = project.estimate.quote.proposal.created_on
    if Order.objects.filter(proposal__quote__estimate__bfm__id=project.id).exists():
        steps_date[0] = 4
        steps_date[3] = project.estimate.quote.proposal.order.date_po_received
        steps_date[4] = project.estimate.quote.proposal.order.estimated_date_of_project
    if Invoice.objects.filter(order__proposal__quote__estimate__bfm__id=project.id).exists():
        steps_date[0] = 5
        steps_date[5] = project.estimate.quote.proposal.order.invoice.date_completed
    if Report.objects.filter(order__proposal__quote__estimate__bfm__id=project.id).exists():
        steps_date[0] = 6
        steps_date[6] = project.estimate.quote.proposal.order.report.report_date
        if Invoice.objects.filter(order__proposal__quote__estimate__bfm__id=project.id).exists():
            steps_date[0] = 7
            steps_date[7] = project.estimate.quote.proposal.order.invoice.created_on
    return steps_date


class ProjectSerializer(serializers.ModelSerializer):
    project_step = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name')
    project_address_line_1 = serializers.CharField(
        source='project.address_line_1')
    project_address_line_2 = serializers.CharField(
        source='project.address_line_2')
    project_city = serializers.CharField(source='project.city')
    project_state = serializers.CharField(source='project.state')
    project_zip = serializers.CharField(source='project.zip')
    estimator_fName = serializers.CharField(
        source='created_by.profile.user.first_name')
    estimator_lName = serializers.CharField(
        source='created_by.profile.user.last_name')

    class Meta:
        model = BidFile
        fields = [
            'id',
            'due_date',
            'uploaded_file',
            'created_on',
            'hidden_for_customer',
            'project_step',
            'project_name',
            'project_address_line_1',
            'project_address_line_2',
            'project_city',
            'project_state',
            'project_zip',
            'estimator_fName',
            'estimator_lName'
        ]

    def get_project_step(self, project):
        return get_project_step(project)

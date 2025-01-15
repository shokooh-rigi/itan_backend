from rest_framework import serializers

from mysite.api.v2.estimator.serializers import EstimateSerializer
from mysite.proposal.models import Proposal


class ProposalSerializer(serializers.ModelSerializer):
    estimate = EstimateSerializer()

    class Meta:
        model = Proposal
        fields = "__all__"

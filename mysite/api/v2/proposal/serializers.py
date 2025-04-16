from rest_framework import serializers

from mysite.api.v2.estimator.serializers import EstimateSerializer
from mysite.proposal.models import Proposal


class ProposalSerializer(serializers.ModelSerializer):
    estimate = EstimateSerializer(read_only=True)
    has_order = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = "__all__"

    def get_has_order(self, obj):
        """
        Check if the proposal has an associated order.
        """
        return obj.has_order

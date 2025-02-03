import datetime

from rest_framework import serializers

from mysite.settlement.models import Settlement


class SettlementSerializer(serializers.ModelSerializer):
    """
    Serializer for Settlement Model.
    """
    contractor_first_name = serializers.CharField(source='contractor.first_name', read_only=True)
    contractor_last_name = serializers.CharField(source='contractor.last_name', read_only=True)

    class Meta:
        model = Settlement
        fields = [
            'id',
            'contractor_first_name',
            'contractor_last_name',
            'created_on',
            'created_by',
            'settlement_start',
            'settlement_end',
            'fixed_expenses',
        ]

    def create(self, validated_data):
        settlement = super().create(validated_data)

        # Calculate and adjust settlement_end
        settlement.settlement_end += datetime.timedelta(
            hours=23,
            minutes=59,
            seconds=59
        )
        settlement.save()

        return settlement

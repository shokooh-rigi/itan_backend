from django.shortcuts import get_object_or_404
from rest_framework import serializers

from mysite.api.v2.core.serializers import PersonSerializer, ProjectSerializer
from mysite.bidfilemgm.models import BidFile, BidAttachment


class BidSerializer(serializers.ModelSerializer):
    customer = PersonSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    has_estimate = serializers.SerializerMethodField()

    class Meta:
        model = BidFile
        fields = [
            "id",
            "type",
            "customer",
            "project",
            "due_date",
            "note",
            "created_by",
            "has_estimate",
        ]

    def get_has_estimate(self, obj):
        return obj.has_estimate


class BidCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for  create Bid model.
    Handles validation and data transformation for creating and updating bid files.
    """

    class Meta:
        model = BidFile
        fields = [
            "customer",
            "project",
            "due_date",
            "note",
            "created_by",
        ]


class BidAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidAttachment
        exclude = ["bid"]  # Exclude bid from request body

    def create(self, validated_data):
        bid_id = self.context["view"].kwargs.get("bid_id")  # Get bid_id from URL
        return BidAttachment.objects.create(bid_id=bid_id, **validated_data)

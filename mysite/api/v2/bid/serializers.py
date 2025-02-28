from django.shortcuts import get_object_or_404
from rest_framework import serializers

from mysite.bidfilemgm.models import BidFile, BidAttachment


class BidSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = BidFile
        fields = [
            "id",
            "type",
            "customer",
            "customer_name",
            "project",
            "project_name",
            "due_date",
            "note",
            "created_by",
        ]


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

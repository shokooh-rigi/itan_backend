import os

from django.conf import settings
from rest_framework import serializers

from mysite.bidfilemgm.models import BidFile
from mysite.s3_file_manager import S3


class BidFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = BidFile
        fields = [
            'customer',
            'project',
            'uploaded_file',
            'due_date',
            'note',
            'created_by',
        ]


class BidFileCreateSerializer(serializers.ModelSerializer):
    """
        Serializer for  create BidFile model.
        Handles validation and data transformation for creating and updating bid files.
        """

    class Meta:
        model = BidFile
        fields = [
            'customer',
            'project',
            'uploaded_file',
            'due_date',
            'note',
            'created_by',
        ]

    def validate_uploaded_file(self, value):
        """
        Custom validation for file size to ensure it doesn't exceed the maximum upload size.
        """
        total_size = sum([f.size for f in value])
        if total_size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("Selected files exceeded maximum upload size!")
        return value

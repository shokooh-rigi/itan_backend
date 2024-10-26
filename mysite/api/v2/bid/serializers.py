from django.conf import settings
from rest_framework import serializers

from mysite.ibfm.models import iBidFile


class BidFileSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(format='%m/%d/%Y', input_formats=['%m/%d/%Y'])
    uploaded_file = serializers.ListField(
        child=serializers.FileField(required=False),
        required=False
    )

    class Meta:
        model = iBidFile
        fields = [
            'customer',
            'project',
            'uploaded_file',
            'due_date',
            'note',
            'created_by',
        ]

    @staticmethod
    def validate_uploaded_file(files):
        """
        Validate the size of uploaded files.
        """
        if files:
            total_size = sum(file.size for file in files)
            if total_size > settings.MAX_UPLOAD_SIZE:
                raise serializers.ValidationError("Selected files exceeded maximum upload size!")
        return files

    def create(self, validated_data):
        """
        Handle the creation of a new BidFile entry.
        """
        files = validated_data.pop('uploaded_file', [])
        bid_file = iBidFile.objects.create(**validated_data)

        # TODO: Add logic for saving files in specific directories
        #  or handling them with a file storage system in the future.
        for file in files:
            bid_file.uploaded_file.save(file.name, file)

        return bid_file


class BidFileUpdateSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(format='%m/%d/%Y', input_formats=['%m/%d/%Y'])

    class Meta:
        model = iBidFile
        fields = [
            'customer',
            'project',
            'due_date',
            'note',
            'created_by',
        ]

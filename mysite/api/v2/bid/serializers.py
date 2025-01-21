from rest_framework import serializers

from mysite.bidfilemgm.models import BidFile


class BidFileSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = BidFile
        fields = [
            'customer',
            'customer_name',
            'project',
            'project_name',
            'uploaded_file',
            'due_date',
            'note',
            'created_by',
            'id',
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

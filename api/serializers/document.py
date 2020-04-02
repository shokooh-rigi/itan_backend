from rest_framework import serializers

from mysite.administrative.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source='type.name')

    class Meta:
        model = Document
        fields = [
            'id',
            'uploaded_file',
            'created_on',
            'type',
            'type_name',
        ]

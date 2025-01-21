from rest_framework import serializers
from mysite.bid.models import Bid


class BidSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id',  # ID is included for retrieval
            'customer',
            'customer_name',  # Read-only field
            'project',
            'project_name',  # Read-only field
            'uploaded_file',
            'due_date',
            'note',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        # Use the context to adjust fields dynamically
        super().__init__(*args, **kwargs)
        if self.context.get('is_create', False):
            # Exclude 'id' for create operations
            self.fields.pop('id')
            # Exclude read-only fields
            self.fields.pop('customer_name', None)
            self.fields.pop('project_name', None)

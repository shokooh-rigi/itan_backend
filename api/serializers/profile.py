from rest_framework import serializers

from mysite.core.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'title',
            'emp_id',
            'tel',
            'fax',
            'cell',
            'e_sign',
            'pic',
            'wallpaper',
            'stamp',
            'bio',
            'location',
            'birth_date'
        ]


class AddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'physical_address_line_1',
            'physical_address_line_2',
            'physical_city',
            'physical_state',
            'physical_zip',
            'billing_address_line_1',
            'billing_address_line_2',
            'billing_city',
            'billing_state',
            'billing_zip',
        ]

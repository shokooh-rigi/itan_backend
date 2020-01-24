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

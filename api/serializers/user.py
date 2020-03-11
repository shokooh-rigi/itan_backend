from rest_framework import serializers

from custom_user.models import User

from .profile import ProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    password = serializers.SerializerMethodField()
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'first_name',
            'last_name',
            'profile',
        ]

    def get_password(self, obj):
        return ''

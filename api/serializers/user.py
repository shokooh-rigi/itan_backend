from rest_framework import serializers

from custom_user.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'password', 'last_login', 'is_superuser', 'first_name',
                  'last_name', 'is_staff', 'is_active', 'date_joined', 'email']

    def get_password(self, obj):
        return ''

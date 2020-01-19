from rest_framework import serializers

from custom_user.models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = [ 'username', 'email', 'date_joined']

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from custom_user.models import User
from api.serializers import UserSerializer


class UserList(APIView):
    def get(self, request, format=None):
        if request.user.is_authenticated:
            users = User.objects.all().order_by('-date_joined')
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        else:
            return Response('Forbidden 403', status=status.HTTP_403_FORBIDDEN)

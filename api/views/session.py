from django.contrib.auth import logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.user import UserSerializer


class SessionAPIView(AuthenticationMixin, APIView):

    # Fetch Session information
    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Create a new Session
    def post(self, request, format=None):
        pass

    # Close the Session
    def delete(self, request, format=None):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

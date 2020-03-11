from django.contrib.auth import logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.user import UserSerializer


class SessionAPIView(AuthenticationMixin, APIView):

    def get(self, request, format=None):
        """Fetch Session information"""

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a new Session"""

        pass

    def delete(self, request, format=None):
        """Close the Session"""

        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

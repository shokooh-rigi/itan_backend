from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..serializers.user import UserSerializer


class SessionAPIView(APIView):
    serializer_class = UserSerializer

    def get(self, request, format=None):
        """Fetch Session information"""

        if request.user.is_authenticated:
            serializer = self.serializer_class(request.user)
            return Response(serializer.data)
        return Response('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        """Create a new Session"""

        email = request.data.get('email', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
        return self.get(request, format)

    def delete(self, request, format=None):
        """Close the Session"""

        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

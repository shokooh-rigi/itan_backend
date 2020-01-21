from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..serializers.user import UserSerializer


class SessionAPIView(APIView):

    # Fetch Session information
    def get(self, request, format=None):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        else:
            return Response('Not Found', status=status.HTTP_404_NOT_FOUND)

    # Create a new Session
    def post(self, request, format=None):
        pass

    # Close the Session
    def delete(self, request, format=None):
        pass

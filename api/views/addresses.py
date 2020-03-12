from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.profile import AddressesSerializer


class AddressesAPIView(AuthenticationMixin, APIView):
    serializer_class = AddressesSerializer

    def get(self, request, format=None):
        """Get the Profile addresses fields"""

        serializer = self.serializer_class(request.user.profile)
        return Response(serializer.data)

    def put(self, request, format=None):
        """Update the Profile addresses fields"""

        serializer = self.serializer_class(request.user.profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response('Input object is not an instance of Profile Addresses.', status=status.HTTP_400_BAD_REQUEST)

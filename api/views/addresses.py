from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from custom_user.models import User
from mysite.core.forms import AddressesForm

from ..serializers.profile import AddressesSerializer


class ProfilesAPIView(APIView):

    def update_addresses(self, request):
        address_form = AddressesForm(request.data, instance=request.user)
        if address_form.is_valid():
            address_form.save()
            return True
        else:
            return False

    # Update the Profile and the User(first_name, last_name)
    def put(self, request, format=None):
        if request.user.is_authenticated:
            if self.update_addresses(request):
                user = User.objects.get(pk=request.user.pk)
                serializer = AddressesSerializer(user.profile)
                return Response(serializer.data)
            else:
                return Response('Something went wrong while saving changes.', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)

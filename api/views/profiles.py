from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from custom_user.models import User
from mysite.core.forms import UserForm, ProfileForm

from ..authentication_mixin import AuthenticationMixin
from ..serializers.user import UserSerializer


class ProfilesAPIView(AuthenticationMixin, APIView):

    def update_user_and_profile(self, request):
        user_form = UserForm(request.data, instance=request.user)
        profile_form = ProfileForm(
            request.data, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return True
        else:
            return False

    def put(self, request, format=None):
        """Update the Profile and the User(first_name, last_name)"""

        if self.update_user_and_profile(request):
            user = User.objects.get(pk=request.user.pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
            return Response('Something went wrong while saving changes.', status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth import update_session_auth_hash
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.user import UserSerializer


class UsersAPIView(AuthenticationMixin, APIView):
    serializer_class = UserSerializer

    def _change_password(self, user, request):
        data = request.data
        new_password = data.get('password', '')
        current_password = data.get('current_password', '')
        if new_password and current_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                update_session_auth_hash(request, user)
            else:
                raise ValueError(
                    'Your old password was entered incorrectly. Please enter it again.')

    def put(self, request, format=None):
        """Update a User"""

        user = request.user
        serializer = self.serializer_class(user, data=request.data)
        if serializer.is_valid():
            try:
                self._change_password(user, request)
                serializer.save()
                return Response(serializer.data)
            except ValueError as error:
                return Response(error.args[0], status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('Input object is not an instance of User.', status=status.HTTP_400_BAD_REQUEST)

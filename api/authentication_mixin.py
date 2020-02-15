from django.http import HttpResponse
from rest_framework import status


class AuthenticationMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponse('401 Unauthorized', status=status.HTTP_401_UNAUTHORIZED)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.business_checking_account import BusinessCheckingAccountSerializer
from mysite.core.models import BusinessCheckingAccount


class BusinessCheckingAccountAPIView(AuthenticationMixin, APIView):
    serializer_class = BusinessCheckingAccountSerializer

    def _get_obj(self, request, pk):
        return BusinessCheckingAccount.objects.get(pk=pk, user=request.user.profile)

    def _http_404_not_found(self):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk=None, format=None):
        """Get the BusinessCheckingAccount object/list"""

        if pk != None:
            try:
                account = self._get_obj(request, pk)
                serializer = self.serializer_class(account, many=False)
                return Response(serializer.data)
            except BusinessCheckingAccount.DoesNotExist:
                return self._http_404_not_found()
        else:
            accounts = BusinessCheckingAccount.objects.filter(
                user=request.user.profile)
            serializer = self.serializer_class(accounts, many=True)
            return Response(serializer.data)

    def post(self, request, pk=None, format=None):
        """Create a BusinessCheckingAccount"""

        return self.put(request, None, format)

    def put(self, request, pk=None, format=None):
        """Update/Create the BusinessCheckingAccount"""

        if pk != None:
            try:
                account = self._get_obj(request, pk)
            except BusinessCheckingAccount.DoesNotExist:
                return self._http_404_not_found()
        else:
            account = BusinessCheckingAccount()

        data = request.data.copy()
        data['user'] = str(request.user.profile.pk)
        serializer = self.serializer_class(account, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        """Delete the BusinessCheckingAccount"""

        if pk != None:
            try:
                account = self._get_obj(request, pk)
                account.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except BusinessCheckingAccount.DoesNotExist:
                return self._http_404_not_found()
        return self._http_404_not_found()

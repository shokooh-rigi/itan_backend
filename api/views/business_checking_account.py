from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.business_checking_account import BusinessCheckingAccountSerializer
from mysite.core.models import BusinessCheckingAccount


class BusinessCheckingAccountAPIView(AuthenticationMixin, APIView):
    serializer_class = BusinessCheckingAccountSerializer

    def _get_account(self, request, pk):
        return get_object_or_404(BusinessCheckingAccount, pk=pk, user=request.user.profile)

    def _get_all_accounts(self, request):
        return BusinessCheckingAccount.objects.filter(user=request.user.profile)

    def get(self, request, pk=None, format=None):
        """Get the BusinessCheckingAccount object/list"""

        if pk != None:
            account = self._get_account(request, pk)
            serializer = self.serializer_class(account, many=False)
            return Response(serializer.data)
        else:
            accounts = self._get_all_accounts(request)
            serializer = self.serializer_class(accounts, many=True)
            return Response(serializer.data)

    def post(self, request, pk=None, format=None):
        """Create a BusinessCheckingAccount"""

        return self.put(request, None, format)

    def put(self, request, pk=None, format=None):
        """Update/Create the BusinessCheckingAccount"""

        if pk != None:
            account = self._get_account(request, pk)
        else:
            account = BusinessCheckingAccount()

        request.data['user'] = str(request.user.profile.pk)
        serializer = self.serializer_class(account, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        """Delete the BusinessCheckingAccount"""

        account = self._get_account(request, pk)
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

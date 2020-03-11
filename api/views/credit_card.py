from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.credit_card import CreditCardSerializer
from mysite.core.models import CreditCard


class CreditCardAPIView(AuthenticationMixin, APIView):
    serializer_class = CreditCardSerializer

    def _get_card(self, request, pk):
        return get_object_or_404(CreditCard, pk=pk, user=request.user.profile)

    def _get_all_cards(self, request):
        return CreditCard.objects.filter(user=request.user.profile)

    def get(self, request, pk=None, format=None):
        """Get the CreditCard object/list"""

        if pk != None:
            card = self._get_card(request, pk)
            serializer = self.serializer_class(card, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            cards = self._get_all_cards(request)
            serializer = self.serializer_class(cards, many=True)
            return Response(serializer.data)

    def post(self, request, pk=None, format=None):
        """Create a CreditCard"""

        all_cards = self._get_all_cards(request)
        if not all_cards.exists():
            request.data['default_card'] = True
        return self.put(request, None, format)

    def put(self, request, pk=None, format=None):
        """Update/Create the CreditCard"""

        if pk != None:
            card = self._get_card(request, pk)
        else:
            card = CreditCard()

        request.data['user'] = str(request.user.profile.pk)
        serializer = self.serializer_class(card, data=request.data)
        if serializer.is_valid():
            serializer.save()
            if card.default_card == True:
                self._get_all_cards(request).filter(
                    ~Q(pk=card.pk)).update(default_card=False)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        """Delete the CreditCard"""

        card = self._get_card(request, pk)
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

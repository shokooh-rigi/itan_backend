from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.credit_card import CreditCardSerializer
from mysite.core.models import CreditCard


class CreditCardAPIView(AuthenticationMixin, APIView):
    serializer_class = CreditCardSerializer

    def _get_obj(self, request, pk):
        return CreditCard.objects.get(pk=pk, user=request.user.profile)

    def _http_404_not_found(self):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    # Get the CreditCard object/list
    def get(self, request, pk=None, format=None):
        if pk != None:
            try:
                card = self._get_obj(request, pk)
                serializer = self.serializer_class(card, many=False)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except CreditCard.DoesNotExist:
                return self._http_404_not_found()
        else:
            cards = CreditCard.objects.filter(user=request.user.profile)
            serializer = self.serializer_class(cards, many=True)
            return Response(serializer.data)

    # Create a CreditCard
    def post(self, request, pk=None, format=None):
        all_cards = CreditCard.objects.filter(user=request.user.profile)
        if not all_cards.exists():
            request.data['default_card'] = True
        return self.put(request, None, format)

    # Update/Create the CreditCard
    def put(self, request, pk=None, format=None):
        if pk != None:
            try:
                card = self._get_obj(request, pk)
            except CreditCard.DoesNotExist:
                return self._http_404_not_found()
        else:
            card = CreditCard()

        request.data['user'] = str(request.user.profile.pk)
        serializer = self.serializer_class(card, data=request.data)
        if serializer.is_valid():
            serializer.save()

            if card.default_card == True:
                other_cards = CreditCard.objects.filter(
                    ~Q(pk=card.pk), user=request.user.profile)
                for user_card in other_cards:
                    user_card.default_card = False
                    user_card.save()

            return Response(serializer.data)
        else:
            # 'Something went wrong while saving changes.'
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Delete the CreditCard
    def delete(self, request, pk=None, format=None):
        if pk != None:
            try:
                card = self._get_obj(request, pk)
                card.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except CreditCard.DoesNotExist:
                return self._http_404_not_found()
        return self._http_404_not_found()

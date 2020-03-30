from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework import status

from ..authentication_mixin import AuthenticationMixin
from ..serializers.invoice import InvoiceSerializer
from mysite.gi.models import Invoice


class InvoicesAPIView(AuthenticationMixin, APIView):
    serializer_class = InvoiceSerializer

    def _get_invoice(self, request, pk):
        return get_object_or_404(Invoice, pk=pk, mark_as_paid=False, order__proposal__quote__estimate__bfm__customer=request.user.profile.customer)

    def _get_all_invoices(self, request):
        return Invoice.objects.filter(mark_as_paid=False, order__proposal__quote__estimate__bfm__customer=request.user.profile.customer)

    def get(self, request, pk=None, format=None):
        """Get the Invoice object/list"""

        if pk != None:
            invoice = self._get_invoice(request, pk)
            serializer = self.serializer_class(invoice, many=False)
            return Response(serializer.data)
        else:
            invoices = self._get_all_invoices(request)
            serializer = self.serializer_class(invoices, many=True)
            return Response(serializer.data)

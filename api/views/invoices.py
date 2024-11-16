import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response

from mysite.gi.models import Invoice

from ..authentication_mixin import AuthenticationMixin
from ..serializers.invoice import InvoiceSerializer
from ..pagination import CustomPageNumberPagination


class InvoicesAPIView(AuthenticationMixin, APIView):
    serializer_class = InvoiceSerializer

    def _get_invoice(self, request, pk):
        return get_object_or_404(self._get_all_invoices(request), pk=pk)

    def _get_all_invoices(self, request):
        return Invoice.objects.filter(mark_as_paid=False, order__proposal__estimate__bfm__customer=request.user.profile.customer)

    def _filter_invoices(self, request, invoices):
        """Filter the invoices"""

        # filter = {
        #     'search': request.query_params.get('search', ''),
        #     'fromDate': request.query_params.get('fromDate', ''),
        #     'toDate': request.query_params.get('toDate', ''),
        #     'ordering': request.query_params.get('ordering', ''),
        #     'asc': True if request.query_params.get('asc', 'true') == 'true' else False
        # }

        # if filter['search']:
        #     invoices = invoices.filter(
        #         Q(project__name__icontains=filter['search']))

        # if filter['fromDate'] and filter['toDate']:
        #     from_date_obj = datetime.datetime.strptime(
        #         filter['fromDate'], '%m/%d/%Y')
        #     to_date_obj = datetime.datetime.strptime(
        #         filter['toDate'], '%m/%d/%Y')
        #     to_date_obj = to_date_obj + \
        #         datetime.timedelta(hours=23, minutes=59, seconds=59)
        #     invoices = invoices.filter(
        #         project__created_on__range=(from_date_obj, to_date_obj))

        # if filter['ordering']:
        #     invoices = invoices.order_by(
        #         ('' if filter['asc'] else '-') + 'project__' + filter['ordering'])

        return invoices

    def get(self, request, pk=None, format=None):
        """Get the Invoice object/list"""

        if pk != None:
            invoice = self._get_invoice(request, pk)
            serializer = self.serializer_class(invoice, many=False)
            return Response(serializer.data)
        else:
            invoices = self._get_all_invoices(request)
            invoices = self._filter_invoices(request, invoices)
            paginator = CustomPageNumberPagination()
            return paginator.get_paginated_response(invoices, request, self.serializer_class)

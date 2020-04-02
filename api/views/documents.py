from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from mysite.administrative.models import Document

from ..authentication_mixin import AuthenticationMixin
from ..serializers.document import DocumentSerializer


class DocumentAPIView(AuthenticationMixin, APIView):
    serializer_class = DocumentSerializer

    def _get_document(self, request, pk):
        return get_object_or_404(self._get_all_documents(request), pk=pk)

    def _get_all_documents(self, request):
        user_company = request.user.profile.customer.company
        return Document.objects.filter(customer=user_company)

    def get(self, request, pk=None, format=None):
        """Get the Document object/list"""

        if pk != None:
            document = self._get_document(request, pk)
            serializer = self.serializer_class(document, many=False)
            return Response(serializer.data)
        else:
            documents = self._get_all_documents(request)
            serializer = self.serializer_class(documents, many=True)
            return Response(serializer.data)

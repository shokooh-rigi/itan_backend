from rest_framework.generics import ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMessage

from mysite.coi.models import Coi
from mysite.core.models import ModulesToEmailTemplateRelation
from mysite.core.views import htmlbodytemplate_tag_converter
from .serializers import CoiSerializer


class CoiListView(ListAPIView):
    """
    API endpoint to list COI objects with pagination.
    """
    serializer_class = CoiSerializer
    queryset = Coi.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle optional ordering
        ordering = self.request.query_params.get('ordering', 'created_on')
        return self.queryset.order_by(ordering)


class CoiCreateView(APIView):
    """
    API endpoint to create a COI object and send an email.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        form_data = request.data
        serializer = CoiSerializer(data=form_data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save COI object
        new_coi = serializer.save()

        # Email logic
        to_email = form_data.get('email', '').replace(" ", "").replace(";", ",").split(',')
        cc = form_data.get('cc', '').replace(" ", "").replace(";", ",").split(',')
        subject = form_data.get('subject', 'Default Subject')

        # Get body and footer templates
        if ModulesToEmailTemplateRelation.objects.filter(module=6).exists():
            body_content = ModulesToEmailTemplateRelation.objects.get(module=6).template.content
        else:
            body_content = "There was no email template defined for 'COI'."
        body_content = htmlbodytemplate_tag_converter(2, body_content, request, new_coi)

        if ModulesToEmailTemplateRelation.objects.filter(module=5).exists():
            footer_content = ModulesToEmailTemplateRelation.objects.get(module=5).template.content
        else:
            footer_content = "There was no email template defined for 'Email Footer'."
        footer_content = htmlbodytemplate_tag_converter(2, footer_content, request, new_coi)

        # Construct and send the email
        message = body_content + '<br />' + footer_content
        email = EmailMessage(
            subject,
            message,
            'estimator@tabtechinc.com',
            to_email,
            cc=cc if cc != [''] else None
        )
        email.content_subtype = "html"
        email.send()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CoiUpdateView(UpdateAPIView):
    """
    API endpoint to update a COI object.
    """
    serializer_class = CoiSerializer
    queryset = Coi.objects.all()
    permission_classes = [IsAuthenticated]


class CoiDeleteView(DestroyAPIView):
    """
    API endpoint to delete a COI object.
    """
    queryset = Coi.objects.all()
    permission_classes = [IsAuthenticated]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.core.models import Project
from mysite.bidfilemgm.forms import BidFileForm

from ..authentication_mixin import AuthenticationMixin


class BidFilesAPIView(AuthenticationMixin, APIView):

    def _save_bidfile(self, request):
        data = request.POST.copy()
        data['created_by'] = request.user.pk
        data['customer'] = request.user.profile.customer.pk

        form = BidFileForm(data, request.FILES or None)
        try:
            if form.is_valid():
                project = Project(
                    name=form.cleaned_data['project_name'], created_by=request.user)
                project.save()
                entry = form.save(commit=False)
                entry.project = project
                entry.save()
                return True
            else:
                return False
        except:
            return False

    # Create a new BidFile (and a Project)
    def post(self, request, format=None):
        if self._save_bidfile(request):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response('Something went wrong while saving Bid File.', status=status.HTTP_400_BAD_REQUEST)

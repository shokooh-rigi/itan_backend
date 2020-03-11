import zipfile
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.core.models import Project
from mysite.bidfilemgm.forms import BidFileForm

from ..authentication_mixin import AuthenticationMixin


class BidFilesAPIView(AuthenticationMixin, APIView):
    def _handle_uploaded_file(self, f, file_path):
        destination = open(file_path, 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

    def _create_zip_file(self, filenames, path, project_name):
        zip_filename = os.path.join(path, project_name)
        zf = zipfile.ZipFile(zip_filename, "w")
        for file in filenames:
            fdir, fname = os.path.split(file)
            zf.write(file, fname)
            os.remove(file)
        zf.close()
        return zf

    def _save_bidfile(self, request):
        data = request.POST.copy()
        data['created_by'] = request.user.pk
        data['customer'] = request.user.profile.customer.pk

        form = BidFileForm(data, request.FILES or None)
        try:
            if form.is_valid():
                temp_path = os.path.join(os.path.abspath(
                    os.path.dirname("__file__")), "media/uploads/bidfiles")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                files_list = request.FILES.getlist('uploaded_file')
                files = []
                for f in files_list:
                    files.append(os.path.join(temp_path, f.name))
                    self._handle_uploaded_file(f, files[-1])

                project = Project(
                    name=form.cleaned_data['project_name'], created_by=request.user)
                project.save()
                new_bidfile = form.save(commit=False)
                new_bidfile.project = project
                new_bidfile.save()

                zip_file_name = str(new_bidfile.pk) + '. ' + \
                    form.cleaned_data['project_name'] + '.zip'
                myzip = self._create_zip_file(files, temp_path, zip_file_name)
                os.remove(new_bidfile.uploaded_file.path)
                new_bidfile.uploaded_file = myzip.filename
                new_bidfile.save()
                return True
            else:
                return False
        except:
            return False

    def post(self, request, format=None):
        """Create a new BidFile (and a Project)"""

        if self._save_bidfile(request):
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response('Something went wrong while saving Bid File.', status=status.HTTP_400_BAD_REQUEST)

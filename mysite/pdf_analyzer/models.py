import os
from urllib.parse import urljoin
import json

from django.core.exceptions import SuspiciousFileOperation
from django.db import models
from django.utils.encoding import filepath_to_uri
from django.conf import settings

from mysite.ibfm.models import iBidFile

MAX_TEXT_LENGTH = 4096


def safe_join(base, *paths):
    """
    Join one or more path components to the base path component intelligently.
    Return a normalized, absolute version of the final path.

    Raise ValueError if the final path isn't located inside of the base path
    component.
    """
    final_path = os.path.abspath(os.path.join(base, *paths))
    base_path = os.path.abspath(base)
    # Ensure final_path starts with base_path (using normcase to ensure we
    # don't false-negative on case insensitive operating systems like Windows),
    # further, one of the following conditions must be true:
    #  a) The next character is the path separator (to prevent conditions like
    #     safe_join("/dir", "/../d"))
    #  b) The final path must be the same as the base path.
    #  c) The base path must be the most root path (meaning either "/" or "C:\\")
    if (not os.path.normcase(final_path).startswith(os.path.normcase(base_path + os.path.sep)) and
            os.path.normcase(final_path) != os.path.normcase(base_path) and
            os.path.dirname(os.path.normcase(base_path)) != os.path.normcase(base_path)):
        raise SuspiciousFileOperation(
            'The joined path ({}) is located outside of the base path '
            'component ({})'.format(final_path, base_path))
    return final_path


class AddressExtractionRun(models.Model):
    file = models.ForeignKey(iBidFile, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    processed_images = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    process_variables = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    addresses = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    execution_time = models.IntegerField(null=True)
    run_step = models.SmallIntegerField(default=1)
    run_step_progress = models.SmallIntegerField(default=-1)
    is_finished = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    base_url = settings.MEDIA_URL
    base_location = settings.MEDIA_ROOT
    save_files_to = 'pdf_analyzer/address_extraction'

    def get_path(self, file_name: str) -> str:
        return safe_join(os.path.abspath(self.base_location), file_name)

    def get_url(self, file_name: str) -> str:
        url = filepath_to_uri(file_name)
        if url is not None:
            url = url.lstrip('/')
        return urljoin(self.base_url, url)

    def get_processed_images_url(self) -> str:
        images = json.loads(self.processed_images)
        images_url = {}
        for page, image in images.items():
            images_url[page] = {
                'width': image['width'],
                'height': image['height'],
                'url': self.get_url(image['url'])
            }
        return json.dumps(images_url)

    def file_name(self):
        return os.path.basename(self.file.uploaded_file.file.name)

    class Meta:
        ordering = ['-created_on']


class AddressExtractionDebug(models.Model):
    run = models.ForeignKey(AddressExtractionRun, on_delete=models.CASCADE)
    debug_step = models.SmallIntegerField()
    data = models.CharField(max_length=MAX_TEXT_LENGTH)

    class Meta:
        ordering = ['run', 'debug_step']
        unique_together = ['run', 'debug_step']

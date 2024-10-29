import datetime
from django.conf import settings
from django.db import models

from mysite.core.models import Person, User, Project


class iBidFile(models.Model):
    customer = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        help_text="Maximum Upload Size: " + str(settings.MAX_UPLOAD_SIZE / 1048576) + "MB",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    due_date = models.DateField(
        default=datetime.datetime.now().strftime("%m/%d/%Y"),
        blank=False,
        null=True,
    )
    # Todo: check this path work from settings?
    uploaded_file = models.FileField(
        upload_to=settings.UPLOAD_BID_FILE_PATH,
        blank=True,
        null=True,
    )
    note = models.TextField(
        max_length=255,
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False,
    )
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)
    archive = models.BooleanField(default=False)
    hidden_for_customer = models.BooleanField(default=False)

    class Meta:
        ordering = ["-due_date"]
        verbose_name = 'Bid Files Management'
        verbose_name_plural = 'Bid Files Management'

    def __str__(self):
        return str(self.id) + ' - ' + self.customer.company.name + ': ' + str(self.project)

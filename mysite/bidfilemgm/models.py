import datetime

from django.conf import settings
from django.db import models

from mysite.core.base_model import BaseModel
from mysite.core.models import Person, User, Project


class BidFile(BaseModel):
    """
        Model representing ibid files associated with a customer and project.
        Includes details such as the customer, project, due date, uploaded file,
        creator, and additional notes. Also contains flags for archiving and
        controlling visibility to customers.
        """

    customer = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        help_text="Maximum Upload Size: " + str(settings.MAX_UPLOAD_SIZE / 1048576) + "MB",
    )
    # todo: whats this hard code : 1048576 ????

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
    uploaded_file = models.FileField(
        upload_to=settings.UPLOAD_BID_FILE_PATH,
        blank=True,
        null=True,
    )
    note = models.TextField(max_length=1000, blank=True, null=True)
    hidden_for_customer = models.BooleanField(default=False)

    class Meta:
        ordering = ["-due_date"]
        verbose_name = 'Bid Files Management'
        verbose_name_plural = 'Bid Files Managements'

    def __str__(self):
        return str(self.id) + ' - ' + self.customer.company.name + ': ' + str(self.project)


class EquipmentSubmittal(BaseModel):
    """
       Model representing an equipment submittal associated with a ibid file.
       Stores the file related to equipment and tracks the creation timestamp.
       """
    bidfile = models.OneToOneField(
        BidFile,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
    )
    uploaded_file = models.FileField(
        upload_to=settings.UPLOAD_EQUIPMENT_SUBMITTAL_PATH,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.bidfile

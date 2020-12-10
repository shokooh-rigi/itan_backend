import datetime
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from djrichtextfield.models import RichTextField
from ..order.models import Order
from custom_user.models import User
from django.db import models
from tinymce.models import HTMLField
from .validators import validate_file_extension


class ReportSheet(models.Model):
    project = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=False)
    report_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=False)
    general_notes_and_comments = HTMLField(default="The systems described here in this report are operating per design intent.")
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project.project_number


class ReportDrawing(models.Model):
    report_sheet = models.ForeignKey(ReportSheet, on_delete=models.CASCADE, blank=False, null=False)
    drawing_file = models.FileField(upload_to='uploads/drawings', validators=[validate_file_extension])
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id) + ' ' + str(self.report_sheet)

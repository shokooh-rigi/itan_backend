import datetime
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from djrichtextfield.models import RichTextField
from ..order.models import Order
from custom_user.models import User
from django.db import models
from tinymce.models import HTMLField
from .validators import validate_file_extension, validate_img_extension
from .render import Render

REPORT_TYPE_CHOICES = (
        (1, 'Automatic'),
        (2, 'Manual'),
        (3, 'Import'),
    )


class ReportSheet(models.Model):
    project = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=False)
    report_date = models.DateField(default=datetime.datetime.now(), blank=False, null=False)
    revised_date = models.DateField(blank=True, null=True)
    last_report_date = models.DateField(blank=True, null=True)
    cover_report_date = models.DateField(blank=True, null=True)
    upload_table_of_content = models.FileField(upload_to='uploads/table_of_contents', blank=True, null=True, validators=[validate_file_extension])
    upload_test_sheets = models.FileField(upload_to='uploads/testsheet_reports', blank=True, null=True, validators=[validate_file_extension])
    upload_drawing_pdf = models.FileField(upload_to='uploads/drawing_pdfs', blank=True, null=True, validators=[validate_file_extension])
    report_type = models.PositiveSmallIntegerField(choices=REPORT_TYPE_CHOICES, default=1)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project.project_number

    @classmethod
    def create_cover_pdf(cls, parameters):
        cover_pdf = Render.render_to_file('pdfTemplates/coverTemplate.html', parameters, 'report')
        return cover_pdf

    @classmethod
    def create_report_pdf(cls, parameters):
        report_pdf = Render.render_to_file('pdfTemplates/reportTemplate.html', parameters, 'report')
        return report_pdf

    @classmethod
    def delete_report_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'report')
        return delete_pdf
    
    class Meta:
        ordering = ['-report_date', 'project']


# class ReportDrawing(models.Model):
#     report_sheet = models.ForeignKey(ReportSheet, on_delete=models.CASCADE, blank=False, null=False)
#     drawing_file = models.FileField(upload_to='uploads/drawings', validators=[validate_file_extension])
#     created_on = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return str(self.id) + ' ' + str(self.report_sheet)

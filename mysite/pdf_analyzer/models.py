from django.db import models

from mysite.ibfm.models import iBidFile

MAX_TEXT_LENGTH = 4096


class AddressExtractionRun(models.Model):
    file = models.ForeignKey(iBidFile, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    processed_images = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    process_variables = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    addresses = models.CharField(max_length=MAX_TEXT_LENGTH, null=True)
    execution_time = models.IntegerField(null=True)
    run_step = models.SmallIntegerField(default=1)
    run_step_progress = models.SmallIntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)


class AddressExtractionDebug(models.Model):
    run = models.ForeignKey(AddressExtractionRun, on_delete=models.CASCADE)
    debug_step = models.SmallIntegerField()
    data = models.CharField(max_length=MAX_TEXT_LENGTH)

    class Meta:
        unique_together = ['run', 'debug_step']

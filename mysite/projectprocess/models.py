from mysite.order.models import *

# Create your models here.


class ProjectProcess(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False, null=False, unique=True)
    tech_package = models.BooleanField(default=False, blank=False, null=False)
    tech_package_date = models.DateTimeField(blank=True, null=True)
    tech_scheduled = models.BooleanField(default=False, blank=False, null=False)
    tech_scheduled_date = models.DateTimeField(blank=True, null=True)
    job_completed = models.BooleanField(default=False, blank=False, null=False)
    job_completed_date = models.DateTimeField(blank=True, null=True)
    report_out = models.BooleanField(default=False, blank=False, null=False)
    report_out_date = models.DateTimeField(blank=True, null=True)
    invoiced = models.BooleanField(default=False, blank=False, null=False)
    invoiced_date = models.DateTimeField(blank=True, null=True)
    completed = models.BooleanField(default=False, blank=False, null=False)
    completed_date = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Project Process'
        verbose_name_plural = 'Project Process'

    def __str__(self):
        return self.order.project_number

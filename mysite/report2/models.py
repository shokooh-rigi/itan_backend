from custom_user.models import User
from mysite.order.models import *


# Create your models here.


class Report(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False)
    report_date = models.DateField(blank=False, null=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Report List"
        verbose_name_plural = "Report List"

    def __str__(self):
        return self.order.project_number

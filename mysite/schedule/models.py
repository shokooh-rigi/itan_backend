from mysite.order.models import *

# Create your models here.


class Schedule(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False, null=False, unique=True)
    assigned_to_employee = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                             related_name='assigned_to_employee')
    assigned_to_contractor = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    scheduled_for = models.DateTimeField(blank=False, null=False)
    archive = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Schedule List'
        verbose_name_plural = 'Schedule List'

    def __str__(self):
        return self.order.project_number

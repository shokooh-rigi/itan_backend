from django.db import models
from mysite.core.models import *
from mysite.estimator.models import *

# Create your models here.


class Order(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, blank=False)
    project_number = models.CharField(max_length=10, blank=False, null=False)
    architect_name = models.CharField(max_length=100, blank=True, null=True)
    po_number = models.CharField(max_length=30, blank=False)
    date_po_received = models.DateField(blank=True, null=True)
    estimated_date_of_project = models.DateField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    archive = models.BooleanField(default=False)
    note = models.TextField(max_length=2000, blank=True, null=True)

    class Meta:
        ordering = ["-proposal"]
        verbose_name = 'Order List'
        verbose_name_plural = 'Order List'

    def __str__(self):
        return estimate_number_generator(self.proposal.quote.estimate.id) + "O"


@receiver(post_save, sender=Order)
def update_project_number(sender, instance, created, **kwargs):
    if created:
        new_number = Setting.objects.get(key='Project Number Last Digit')
        new_number.value = int(Setting.objects.get(key='Project Number Last Digit').value) + 1
        new_number.save()
        instance.project_number = Setting.objects.get(key='Project Number Pre Text').value +\
                                  Setting.objects.get(key='Project Number Last Digit').value.zfill(3)
        instance.save()

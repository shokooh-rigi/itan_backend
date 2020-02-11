from django.db import models
from mysite.core.models import Person, User
import datetime

# Create your models here.


class BidFile(models.Model):
    customer = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=False, null=True)
    project = models.CharField(max_length=255, blank=False, null=True)
    due_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=True)
    uploaded_file = models.FileField(upload_to='uploads/bidfiles')
    note = models.TextField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)
    archive = models.BooleanField(default=False)
    hidden_for_customer = models.BooleanField(default=False)

    class Meta:
        ordering = ["-due_date"]
        verbose_name = 'Bid Files Management'
        verbose_name_plural = 'Bid Files Management'

    def __str__(self):
        return self.customer.name + ': ' + self.project

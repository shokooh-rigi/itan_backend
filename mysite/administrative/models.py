from django.db import models

from mysite.core.models import ContactInfo, User
from ..settings import MAX_UPLOAD_SIZE


# Create your models here.


class TypesOfDocument(models.Model):
    name = models.CharField(max_length=255, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    type = models.ForeignKey(TypesOfDocument, on_delete=models.SET_NULL, blank=False, null=True)
    customer = models.ForeignKey(ContactInfo, on_delete=models.SET_NULL, blank=False, null=True,
                                 related_name='doc_customer'
                                 , help_text="Maximum Upload Size: " + str(MAX_UPLOAD_SIZE / 1048576) + "MB")
    uploaded_file = models.FileField(upload_to='uploads/administrative', blank=False, null=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["customer"]
        unique_together = ('type', 'customer',)

    def __str__(self):
        return self.customer.name + ': ' + self.type.name

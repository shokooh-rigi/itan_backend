from django.db import models
from mysite.core.models import Person

# Create your models here.


class Coi(models.Model):
    contractor = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=False, null=True)
    contract_person_name = models.CharField(max_length=55, blank=False)
    email = models.EmailField(max_length=55, blank=False)
    subject = models.CharField(max_length=100, blank=False)
    cc = models.EmailField(max_length=55, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Certificate of Insurance'
        verbose_name_plural = 'Certificate of Insurance'

    def __str__(self):
        return self.email


class InsuranceCompany(models.Model):
    key = models.CharField(max_length=255, blank=False, unique=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Insurance Company Information'
        verbose_name_plural = 'Insurance Company Information'

    def __str__(self):
        return self.key

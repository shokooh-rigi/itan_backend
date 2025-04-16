from django.db import models

from mysite.core.base_model import BaseModelWithCreatedByUser
from mysite.estimator.models import Estimate, estimate_number_generator


class Proposal(BaseModelWithCreatedByUser):
    estimate = models.OneToOneField(
        Estimate,
        on_delete=models.CASCADE,
        blank=False,
    )
    validity = models.IntegerField(blank=False, default=180)
    note = models.TextField(max_length=255, blank=True, null=True)

    @property
    def has_order(self):
        """
        Check if the proposal has an associated order.
        """
        return hasattr(self, "order")

    class Meta:
        ordering = ["-estimate"]
        verbose_name = "Proposal List"
        verbose_name_plural = "Proposal Lists"

    def __str__(self):
        return estimate_number_generator(self.estimate.id) + "Proposal"

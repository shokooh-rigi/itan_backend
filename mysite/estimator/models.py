from mysite.core.models import *
from mysite.bidfilemgm.models import *
import datetime
from .render import Render


# Create your models here.


class Estimate(models.Model):
    bfm = models.OneToOneField(BidFile, on_delete=models.CASCADE, blank=True, null=True)
    customer = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=False, null=True, related_name='cu_person')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=False, null=True)
    engineer = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=False, null=True, related_name='en_person')
    service = models.ManyToManyField(Service, related_name='estimates', blank=False)
    due_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=True)
    confirm_date = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    note = models.TextField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)
    archive = models.BooleanField(default=False)
    hidden_for_customer = models.BooleanField(default=False)

    class Meta:
        ordering = ["-due_date"]
        verbose_name = 'Estimate List'
        verbose_name_plural = 'Estimate List'

    def __str__(self):
        return estimate_number_generator(self.id)

    @classmethod
    def create_estimate_pdf(cls, parameters):
        estimate_pdf = Render.render_to_file('pdfTemplates/estimateTemplate.html', parameters, 'estimate')
        return estimate_pdf

    @classmethod
    def delete_estimate_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'estimate')
        return delete_pdf


class Quote(models.Model):
    estimate = models.OneToOneField(Estimate, on_delete=models.CASCADE, blank=False)
    note = models.TextField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    archive = models.BooleanField(default=False)

    class Meta:
        ordering = ["-estimate"]
        verbose_name = 'Quote List'
        verbose_name_plural = 'Quote List'

    def __str__(self):
        return estimate_number_generator(self.estimate.id) + "Q"

    @classmethod
    def create_quote_pdf(cls, parameters):
        quote_pdf = Render.render_to_file('pdfTemplates/quoteTemplate.html', parameters, 'quote')
        return quote_pdf

    @classmethod
    def delete_quote_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'quote')
        return delete_pdf


class Proposal(models.Model):
    quote = models.OneToOneField(Quote, on_delete=models.CASCADE, blank=False)
    validity = models.IntegerField(blank=False, default=30)
    note = models.TextField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    archive = models.BooleanField(default=False)

    class Meta:
        ordering = ["-quote"]
        verbose_name = 'Proposal List'
        verbose_name_plural = 'Proposal List'

    def __str__(self):
        return estimate_number_generator(self.quote.estimate.id) + "P"

    @classmethod
    def create_proposal_pdf(cls, parameters):
        proposal_pdf = Render.render_to_file('pdfTemplates/proposalTemplate.html', parameters, 'proposal')
        return proposal_pdf

    @classmethod
    def delete_proposal_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'proposal')
        return delete_pdf


class EstimateEquipment(models.Model):
    estimate = models.ForeignKey(Estimate, on_delete=models.SET_NULL, blank=False, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False)
    quantity = models.IntegerField(blank=False)
    price_override = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Estimated Equipment List'
        verbose_name_plural = 'Estimated Equipment List'

    def __str__(self):
        return estimate_number_generator(self.estimate.id) + " " + self.equipment.name


class EstimateDetails(models.Model):
    estimate = models.OneToOneField(Estimate, on_delete=models.CASCADE)
    cs_choices = (
        (0, '0'),
        (1, '1%'),
        (2, '2%'),
        (3, '3%'),
    )
    control_system = models.PositiveSmallIntegerField(choices=cs_choices, default=0)
    hours_choices = (
        (0, 'Regular'),
        (10, 'Saturday/Holiday'),
        (15, 'Sunday'),
    )
    hours = models.PositiveSmallIntegerField(choices=hours_choices, default=0)
    pre_demo = models.FloatField(default=0)
    adjustment = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    remark = models.TextField(max_length=500, blank=True)
    validity = models.IntegerField(blank=False, default=30)
    saved_flag = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Estimated Additional info'
        verbose_name_plural = 'Estimated Additional info'

    def __str__(self):
        return estimate_number_generator(self.estimate.id)


@receiver(post_save, sender=Estimate)
def create_estimate_details(sender, instance, created, **kwargs):
    if created:
        EstimateDetails.objects.create(estimate=instance)


def estimate_number_generator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimator_long_id = estimate.created_by.id + 100
    estimate_date_created = str(estimate.created_on).replace('-', '')[2:8]
    return estimate_date_created + str(estimator_long_id) + str(estimate.id).zfill(3)

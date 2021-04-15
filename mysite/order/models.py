from mysite.estimator.models import *
from ..core.models import *
from ..dbmanagement.models import *

# Create your models here.


class ControlSystemManufacturer(models.Model):
    manufacturer_name = models.CharField(max_length=30, blank=False, null=False)
    contact_name = models.CharField(max_length=255, blank=True)
    tel = models.CharField(max_length=15, blank=True)
    fax = models.CharField(max_length=15, blank=True)
    mail = models.EmailField(max_length=55, blank=True)
    web = models.CharField(max_length=55, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.manufacturer_name


class ControlSystem(models.Model):
    manufacturer = models.ForeignKey(ControlSystemManufacturer, on_delete=models.PROTECT, blank=False, null=False)
    version_number = models.CharField(max_length=30, blank=True, null=True)
    os = models.CharField(max_length=20, blank=True, null=True)
    release_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=True, null=True)
    control_file_url = models.URLField(max_length=255, blank=True, null=True)
    documentation = models.FileField(upload_to='uploads/control_system_documentations', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.manufacturer) + ", " + str(self.version_number)


class Order(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, blank=False)
    project_number = models.CharField(max_length=10, blank=False, null=False)
    architect_name = models.CharField(max_length=100, blank=True, null=True)
    po_number = models.CharField(max_length=30, blank=False)
    date_po_received = models.DateField(blank=True, null=True)
    estimated_date_of_project = models.DateField(blank=True, null=True)
    invoice_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    control_system = models.ForeignKey(ControlSystem, on_delete=models.SET_NULL, blank=True, null=True)
    equipment_submittal = models.FileField(upload_to='uploads/order_equipment_submittal', blank=True, null=True)
    colored_drawing = models.FileField(upload_to='uploads/order_colored_drawing', blank=True, null=True)
    site_pictures = models.FileField(upload_to='uploads/order_site_pictures', blank=True, null=True)
    test_sheets = models.FileField(upload_to='uploads/order_test_sheets', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    archive = models.BooleanField(default=False)
    fully_settled = models.BooleanField(default=False)
    order_settled_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    completion_percentage = models.PositiveIntegerField(default=0,
                                                        validators=[MaxValueValidator(100), MinValueValidator(0)])
    note = models.TextField(max_length=2000, blank=True, null=True)
    partial_job_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["-proposal"]
        verbose_name = 'Order List'
        verbose_name_plural = 'Order List'

    def __str__(self):
        return self.project_number


@receiver(post_save, sender=Order)
def update_project_number(sender, instance, created, **kwargs):
    if created:
        new_number = Setting.objects.get(key='Project Number Last Digit')
        new_number.value = int(Setting.objects.get(key='Project Number Last Digit').value) + 1
        new_number.save()
        instance.project_number = Setting.objects.get(key='Project Number Pre Text').value + \
                                  Setting.objects.get(key='Project Number Last Digit').value.zfill(3)
        instance.save()


class ChangeOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=False, null=True)
    co_number = models.CharField(max_length=30, blank=False, null=False)
    date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return "Change Order #" + str(self.co_number) + " - Amount $" + str(self.amount)


class TechLabel(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False, null=False)
    label_model = models.ForeignKey(TechLabelModel, on_delete=models.PROTECT, blank=False, null=False)
    detailed_drawing = models.BooleanField(default=False)
    schedule_drawing = models.BooleanField(default=False)
    mechanical_drawing = models.BooleanField(default=False)
    tech_test_sheets = models.BooleanField(default=False)
    point_of_contact_name = models.CharField(max_length=50, blank=True, null=True)
    point_of_contact_cell_phone = models.CharField(max_length=15, blank=True, null=True)
    point_of_contact_office_phone = models.CharField(max_length=15, blank=True, null=True)
    schedule_date = models.DateField(blank=True, null=True)
    tech_notes = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.id) + ": " + str(self.order)

    @classmethod
    def create_techlabel_pdf(cls, parameters):
        techlabel_pdf = Render.render_to_file('pdfTemplates/techLabelTemplate.html', parameters, 'techlabel')
        return techlabel_pdf

    # @classmethod
    # def delete_techlabel_pdf(cls, parameters):
    #     delete_pdf = Render.delete_file(parameters, 'techlabel')
    #     return delete_pdf

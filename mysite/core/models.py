from __future__ import unicode_literals
from django.db import models
from custom_user.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from djrichtextfield.models import RichTextField
from creditcards.models import CardNumberField, CardExpiryField
from django.core.validators import MinLengthValidator
from django.forms import TextInput


class CompanyType(models.Model):
    name = models.CharField(max_length=255, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Company Type'
        verbose_name_plural = 'Company Type'

    def __str__(self):
        return self.name


class ContactInfo(models.Model):
    name = models.CharField(max_length=255, blank=False, error_messages={'required': 'Name Required.'})
    tel = models.CharField(max_length=15, blank=True)
    fax = models.CharField(max_length=15, blank=True)
    mail = models.EmailField(max_length=55, blank=True)
    web = models.CharField(max_length=55, blank=True)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=55, blank=True)
    state = models.CharField(max_length=55, blank=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    company_type = models.ForeignKey(CompanyType, on_delete=models.CASCADE,
                                     error_messages={'required': 'You have to specify Company Type.'})
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=False, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Company Contact info'
        verbose_name_plural = 'Company Contact info'

    def __str__(self):
        return self.name


class Person(models.Model):
    company = models.ForeignKey(ContactInfo, on_delete=models.CASCADE, blank=False)
    name = models.CharField(max_length=255, blank=False)
    title = models.CharField(max_length=255, blank=True)
    gender_choices = (
        (1, 'Male'),
        (2, 'Female'),
        (3, 'Other'),
    )
    gender = models.PositiveSmallIntegerField(choices=gender_choices, default=1)
    tel = models.CharField(max_length=15, blank=True)
    fax = models.CharField(max_length=15, blank=True)
    mail = models.EmailField(max_length=55, blank=True)
    web = models.CharField(max_length=55, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=False, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ('company',)
        verbose_name = 'Company Contact Person'
        verbose_name_plural = 'Company Contact Person'

    def __str__(self):
        return self.company.name + ', ' + self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=30, null=True, blank=True)
    emp_id = models.CharField(max_length=10, null=True, blank=True)
    tel = models.CharField(max_length=30, null=True, blank=True)
    fax = models.CharField(max_length=30, null=True, blank=True)
    cell = models.CharField(max_length=30, null=True, blank=True)
    e_sign = models.FileField(upload_to='uploads/users/signs', null=True, blank=True)
    pic = models.FileField(upload_to='uploads/users/profiles', null=True, blank=True)
    wallpaper = models.FileField(upload_to='uploads/users/wallpapers', null=True, blank=True)
    stamp = models.FileField(upload_to='uploads/users/stamps', null=True, blank=True)

    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    email_confirmed = models.BooleanField(default=False)
    USER_TYPE_CHOICES = (
        (1, 'User'),
        (2, 'QAA'),
        (3, 'Admin'),
        (4, 'Project Manager'),
        (5, 'Tech'),
        (6, 'Super User'),
    )
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)
    customer = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=False, null=True,
                                 related_name='profile_customer')
    physical_address_line_1 = models.CharField(max_length=255, blank=False, null=True)
    physical_address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    physical_city = models.CharField(max_length=55, blank=False, null=True)
    physical_state = models.CharField(max_length=55, blank=False, null=True)
    physical_zip = models.CharField(max_length=10, blank=False, null=True)
    billing_address_line_1 = models.CharField(max_length=255, blank=False, null=True)
    billing_address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=55, blank=False, null=True)
    billing_state = models.CharField(max_length=55, blank=False, null=True)
    billing_zip = models.CharField(max_length=10, blank=False, null=True)

    def __str__(self):
        return self.user.email


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class CreditCard(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False, null=False)
    name_of_card = models.CharField(max_length=50, blank=False, null=False)
    card_number = models.CharField(max_length=16, validators=[MinLengthValidator(16)])
    card_expiration_date = CardExpiryField()
    default_card = models.BooleanField(default=False)
    billing_address_line_1 = models.CharField(max_length=255, blank=False, null=True)
    billing_address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=55, blank=False, null=True)
    billing_state = models.CharField(max_length=55, blank=False, null=True)
    billing_zip = models.CharField(max_length=10, blank=False, null=True)

    def __str__(self):
        return str(self.user.user) + ' at ' + str(self.name_of_card)


class BusinessCheckingAccount(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False, null=False)
    name_of_account = models.CharField(max_length=50, blank=False, null=False)
    bank_routing_number = models.CharField(max_length=9, validators=[MinLengthValidator(9)])
    account_number = models.CharField(max_length=17, validators=[MinLengthValidator(17)])
    business_tax_id = models.CharField(max_length=9, validators=[MinLengthValidator(9)])

    def __str__(self):
        return str(self.user.user) + ' at ' + str(self.name_of_account)


class Project(models.Model):
    name = models.CharField(max_length=255, blank=False)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=55, blank=True)
    state = models.CharField(max_length=55, blank=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    tel = models.CharField(max_length=15, blank=True)
    fax = models.CharField(max_length=15, blank=True)
    mail = models.EmailField(max_length=55, blank=True)
    note = models.TextField(max_length=500, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Project Info'
        verbose_name_plural = 'Project Info'

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=255, blank=False)
    priority = models.IntegerField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority"]
        verbose_name = 'Services Offered'
        verbose_name_plural = 'Services Offered'

    def __str__(self):
        return self.name


class TestSheet(models.Model):
    name = models.CharField(max_length=255, blank=False)
    priority = models.IntegerField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority"]
        verbose_name = 'Test Sheet'
        verbose_name_plural = 'Test Sheet'

    def __str__(self):
        return self.name


class Equipment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=False, null=True)
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=255, blank=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    estimate_work = models.IntegerField(default=10, blank=False, null=False, verbose_name='Estimate Work in Minutes')
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = 'Equipment List'
        verbose_name_plural = 'Equipment List'

    def __str__(self):
        return self.name + ' (' + self.service.name + ')'


class LicenseInfo(models.Model):
    key = models.CharField(max_length=255, blank=False, unique=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'License Information'
        verbose_name_plural = 'License Information'

    def __str__(self):
        return self.key


class LicenseFiles(models.Model):
    key = models.CharField(max_length=255, blank=False, unique=True, editable=True)
    value = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'License Information Files'
        verbose_name_plural = 'License Information Files'

    def __str__(self):
        return self.key


class CompanySubmittalForm(models.Model):
    form_name = models.CharField(max_length=255, blank=True)
    form_file = models.FileField(upload_to='uploads/submittalforms')
    related_services = models.ManyToManyField(Service, blank=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Company Submittal Forms'
        verbose_name_plural = 'Company Submittal Forms'

    def __str__(self):
        return self.form_name


class EmailBodyTemplate(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    content = RichTextField(null=True, blank=True, help_text='<b>Current User Information:</b><br />'
                                                             '[user_name]: Logged in user Name | '
                                                             '[user_title]: Logged in user Title | '
                                                             '[user_cel]: Logged in user Cellphone Number | '
                                                             '[user_tel]: Logged in user Telephone Number'
                                                             '<br /><b>Customer Information:</b><br />'
                                                             '[customer_company_name]: Customer Company Name | '
                                                             '[customer_contact_person]: Customer Contact Person | '
                                                             '[customer_email]: Customer Email | '
                                                             '[customer_address_line_1]: Customer Address 2 | '
                                                             '[customer_address_line_2]: Customer Address 1 | '
                                                             '[customer_city]: Customer City | '
                                                             '[customer_state]: Customer State | '
                                                             '[customer_zip]: Customer Zip'
                                                             '<br /><b>Insurance Company Information:</b><br />'
                                                             '[ic_company_name]: Insurance Company Name | '
                                                             '[ic_contact_name]: Insurance Company Contact Name | '
                                                             '[ic_mail]: Insurance Company Email | '
                                                             '[ic_tel]: Insurance Company Telephone | '
                                                             '[ic_fax]: Insurance Company Fax | '
                                                             '[ic_web]: Insurance Company Website | '
                                                             '[ic_address_line_1]: Insurance Company Address 1 | '
                                                             '[ic_address_line_2]: Insurance Company Address 2 | '
                                                             '[ic_city]: Insurance Company City | '
                                                             '[ic_state]: Insurance Company State | '
                                                             '[ic_zip]: Insurance Company Zip')

    class Meta:
        verbose_name = 'Email Body Template'
        verbose_name_plural = 'Email Body Template'

    def __str__(self):
        return self.name


class ModulesToEmailTemplateRelation(models.Model):
    template = models.ForeignKey(EmailBodyTemplate, on_delete=models.PROTECT, blank=False)
    modules_list = (
        (1, 'Estimate'),
        (2, 'Quotation'),
        (3, 'Proposal'),
        (4, 'Invoice'),
        (5, 'Email Footer'),
        (6, 'COI'),
        (7, 'Submittal'),
    )
    module = models.PositiveSmallIntegerField(choices=modules_list, unique=True, blank=False)

    class Meta:
        verbose_name = 'Connect Modules to Email Templates'
        verbose_name_plural = 'Connect Modules to Email Templates'

    def __str__(self):
        return self.get_module_display()


class Setting(models.Model):
    key = models.CharField(max_length=255, blank=False, unique=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return self.key

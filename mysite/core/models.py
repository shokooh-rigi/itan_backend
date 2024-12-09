import uuid

from creditcards.models import CardExpiryField
from django.core.validators import (
    MinLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from tinymce.models import HTMLField

from custom_user.models import User


class UserTypeChoices(models.IntegerChoices):
    CUSTOMER = 0, "Customer"
    TECH = 1, "Tech"
    ESTIMATOR = 2, "Estimator"
    SUPER_TECH = 3, "Super Tech"
    ACCOUNTING = 4, "Accounting"
    SUPER_ADMIN = 5, "Super Admin"


class GenderChoices(models.IntegerChoices):
    MALE = 0, "Male"
    FEMALE = 1, "Female"


class WorkerStatusChoices(models.IntegerChoices):
    EMPLOYEE = 0, "Employee"
    CONTRACTOR = 1, "Contractor"


class CountryCode(models.TextChoices):
    AF = "AF", "Afghanistan"
    AL = "AL", "Albania"
    DZ = "DZ", "Algeria"
    AS = "AS", "American Samoa"
    AD = "AD", "Andorra"
    AO = "AO", "Angola"
    AI = "AI", "Anguilla"
    AQ = "AQ", "Antarctica"
    AG = "AG", "Antigua and Barbuda"
    AR = "AR", "Argentina"
    AM = "AM", "Armenia"
    AW = "AW", "Aruba"
    AU = "AU", "Australia"
    AT = "AT", "Austria"
    AZ = "AZ", "Azerbaijan"
    BS = "BS", "Bahamas"
    BH = "BH", "Bahrain"
    BD = "BD", "Bangladesh"
    BB = "BB", "Barbados"
    BY = "BY", "Belarus"
    PW = "PW", "Belau"
    BE = "BE", "Belgium"
    BZ = "BZ", "Belize"
    BJ = "BJ", "Benin"
    BM = "BM", "Bermuda"
    BT = "BT", "Bhutan"
    BO = "BO", "Bolivia"
    BQ = "BQ", "Bonaire, Saint Eustatius and Saba"
    BA = "BA", "Bosnia and Herzegovina"
    BW = "BW", "Botswana"
    BV = "BV", "Bouvet Island"
    BR = "BR", "Brazil"
    IO = "IO", "British Indian Ocean Territory"
    BN = "BN", "Brunei"
    BG = "BG", "Bulgaria"
    BF = "BF", "Burkina Faso"
    BI = "BI", "Burundi"
    KH = "KH", "Cambodia"
    CM = "CM", "Cameroon"
    CA = "CA", "Canada"
    CV = "CV", "Cape Verde"
    KY = "KY", "Cayman Islands"
    CF = "CF", "Central African Republic"
    TD = "TD", "Chad"
    CL = "CL", "Chile"
    CN = "CN", "China"
    CX = "CX", "Christmas Island"
    CC = "CC", "Cocos (Keeling) Islands"
    CO = "CO", "Colombia"
    KM = "KM", "Comoros"
    CG = "CG", "Congo (Brazzaville)"
    CD = "CD", "Congo (Kinshasa)"
    CK = "CK", "Cook Islands"
    CR = "CR", "Costa Rica"
    HR = "HR", "Croatia"
    CU = "CU", "Cuba"
    CW = "CW", "Curaçao"
    CY = "CY", "Cyprus"
    CZ = "CZ", "Czech Republic"
    DK = "DK", "Denmark"
    DJ = "DJ", "Djibouti"
    DM = "DM", "Dominica"
    DO = "DO", "Dominican Republic"
    EC = "EC", "Ecuador"
    EG = "EG", "Egypt"
    SV = "SV", "El Salvador"
    GQ = "GQ", "Equatorial Guinea"
    ER = "ER", "Eritrea"
    EE = "EE", "Estonia"
    SZ = "SZ", "Eswatini"
    ET = "ET", "Ethiopia"
    FK = "FK", "Falkland Islands"
    FO = "FO", "Faroe Islands"
    FJ = "FJ", "Fiji"
    FI = "FI", "Finland"
    FR = "FR", "France"
    GF = "GF", "French Guiana"
    PF = "PF", "French Polynesia"
    TF = "TF", "French Southern Territories"
    GA = "GA", "Gabon"
    GM = "GM", "Gambia"
    GE = "GE", "Georgia"
    DE = "DE", "Germany"
    GH = "GH", "Ghana"
    GI = "GI", "Gibraltar"
    GR = "GR", "Greece"
    GL = "GL", "Greenland"
    GD = "GD", "Grenada"
    GP = "GP", "Guadeloupe"
    GU = "GU", "Guam"
    GT = "GT", "Guatemala"
    GG = "GG", "Guernsey"
    GN = "GN", "Guinea"
    GW = "GW", "Guinea-Bissau"
    GY = "GY", "Guyana"
    HT = "HT", "Haiti"
    HM = "HM", "Heard Island and McDonald Islands"
    HN = "HN", "Honduras"
    HK = "HK", "Hong Kong"
    HU = "HU", "Hungary"
    IS = "IS", "Iceland"
    IN = "IN", "India"
    ID = "ID", "Indonesia"
    IR = "IR", "Iran"
    IQ = "IQ", "Iraq"
    IE = "IE", "Ireland"
    IM = "IM", "Isle of Man"
    IL = "IL", "Israel"
    IT = "IT", "Italy"
    CI = "CI", "Ivory Coast"
    JM = "JM", "Jamaica"
    JP = "JP", "Japan"
    JE = "JE", "Jersey"
    JO = "JO", "Jordan"
    KZ = "KZ", "Kazakhstan"
    KE = "KE", "Kenya"
    KI = "KI", "Kiribati"
    KW = "KW", "Kuwait"
    KG = "KG", "Kyrgyzstan"
    LA = "LA", "Laos"
    LV = "LV", "Latvia"
    LB = "LB", "Lebanon"
    LS = "LS", "Lesotho"
    LR = "LR", "Liberia"
    LY = "LY", "Libya"
    LI = "LI", "Liechtenstein"
    LT = "LT", "Lithuania"
    LU = "LU", "Luxembourg"
    MO = "MO", "Macao"
    MG = "MG", "Madagascar"
    MW = "MW", "Malawi"
    MY = "MY", "Malaysia"
    MV = "MV", "Maldives"
    ML = "ML", "Mali"
    MT = "MT", "Malta"
    MH = "MH", "Marshall Islands"
    MQ = "MQ", "Martinique"
    MR = "MR", "Mauritania"
    MU = "MU", "Mauritius"
    YT = "YT", "Mayotte"
    MX = "MX", "Mexico"
    FM = "FM", "Micronesia"
    MD = "MD", "Moldova"
    MC = "MC", "Monaco"
    MN = "MN", "Mongolia"
    ME = "ME", "Montenegro"
    MS = "MS", "Montserrat"
    MA = "MA", "Morocco"
    MZ = "MZ", "Mozambique"
    MM = "MM", "Myanmar"
    NA = "NA", "Namibia"
    NR = "NR", "Nauru"
    NP = "NP", "Nepal"
    NL = "NL", "Netherlands"
    NC = "NC", "New Caledonia"
    NZ = "NZ", "New Zealand"
    NI = "NI", "Nicaragua"
    NE = "NE", "Niger"
    NG = "NG", "Nigeria"
    NU = "NU", "Niue"
    NF = "NF", "Norfolk Island"
    KP = "KP", "North Korea"
    MK = "MK", "North Macedonia"
    MP = "MP", "Northern Mariana Islands"
    NO = "NO", "Norway"
    OM = "OM", "Oman"
    PK = "PK", "Pakistan"
    PS = "PS", "Palestinian Territory"
    PA = "PA", "Panama"
    PG = "PG", "Papua New Guinea"
    PY = "PY", "Paraguay"
    PE = "PE", "Peru"
    PH = "PH", "Philippines"
    PN = "PN", "Pitcairn"
    PL = "PL", "Poland"
    PT = "PT", "Portugal"
    PR = "PR", "Puerto Rico"
    QA = "QA", "Qatar"
    RE = "RE", "Reunion"
    RO = "RO", "Romania"
    RU = "RU", "Russia"
    RW = "RW", "Rwanda"
    ST = "ST", "São Tomé and Príncipe"
    BL = "BL", "Saint Barthélemy"
    SH = "SH", "Saint Helena"
    KN = "KN", "Saint Kitts and Nevis"
    LC = "LC", "Saint Lucia"
    SX = "SX", "Saint Martin (Dutch part)"
    MF = "MF", "Saint Martin (French part)"
    PM = "PM", "Saint Pierre and Miquelon"
    VC = "VC", "Saint Vincent and the Grenadines"
    WS = "WS", "Samoa"
    SM = "SM", "San Marino"
    SA = "SA", "Saudi Arabia"
    SN = "SN", "Senegal"
    RS = "RS", "Serbia"
    SC = "SC", "Seychelles"
    SL = "SL", "Sierra Leone"
    SG = "SG", "Singapore"
    SK = "SK", "Slovakia"
    SI = "SI", "Slovenia"
    SB = "SB", "Solomon Islands"
    SO = "SO", "Somalia"
    ZA = "ZA", "South Africa"
    GS = "GS", "South Georgia/Sandwich Islands"
    KR = "KR", "South Korea"
    SS = "SS", "South Sudan"
    ES = "ES", "Spain"
    LK = "LK", "Sri Lanka"
    SD = "SD", "Sudan"
    SR = "SR", "Suriname"
    SJ = "SJ", "Svalbard and Jan Mayen"
    SE = "SE", "Sweden"
    CH = "CH", "Switzerland"
    SY = "SY", "Syria"
    TW = "TW", "Taiwan"
    TJ = "TJ", "Tajikistan"
    TZ = "TZ", "Tanzania"
    TH = "TH", "Thailand"
    TL = "TL", "Timor-Leste"
    TG = "TG", "Togo"
    TK = "TK", "Tokelau"
    TO = "TO", "Tonga"
    TT = "TT", "Trinidad and Tobago"
    TN = "TN", "Tunisia"
    TR = "TR", "Turkey"
    TM = "TM", "Turkmenistan"
    TC = "TC", "Turks and Caicos Islands"
    TV = "TV", "Tuvalu"
    UG = "UG", "Uganda"
    UA = "UA", "Ukraine"
    AE = "AE", "United Arab Emirates"
    GB = "GB", "United Kingdom (UK)"
    US = "US", "United States (US)"
    UM = "UM", "United States (US) Minor Outlying Islands"
    UY = "UY", "Uruguay"
    UZ = "UZ", "Uzbekistan"
    VU = "VU", "Vanuatu"
    VA = "VA", "Vatican"
    VE = "VE", "Venezuela"
    VN = "VN", "Vietnam"
    VG = "VG", "Virgin Islands (British)"
    VI = "VI", "Virgin Islands (US)"
    WF = "WF", "Wallis and Futuna"
    EH = "EH", "Western Sahara"
    YE = "YE", "Yemen"
    ZM = "ZM", "Zambia"
    ZW = "ZW", "Zimbabwe"
    AX = "AX", "Åland Islands"


class BaseAbstractModel(models.Model):
    archive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        related_name="%(class)s_created_by",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class CompanyType(BaseAbstractModel):
    """Represents all company types in this system."""

    name = models.CharField(max_length=100, blank=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Address(BaseAbstractModel):
    """Represents address in database."""

    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=55, blank=True)
    state = models.CharField(max_length=55, blank=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(
        max_length=2, choices=CountryCode.choices, default=CountryCode.US
    )


class ContactInfo(BaseAbstractModel):
    """Represents contact information in database."""

    tel = models.CharField(max_length=15, blank=True, null=True)
    cel = models.CharField(max_length=30, null=True, blank=True)
    fax = models.CharField(max_length=15, blank=True, null=True)
    mail = models.EmailField(max_length=55, blank=True, null=True)
    web = models.CharField(max_length=55, blank=True, null=True)


class Company(BaseAbstractModel):
    """Represents company details."""

    name = models.CharField(max_length=255, blank=False, null=False)
    company_type = models.ForeignKey(
        CompanyType, on_delete=models.PROTECT, blank=False, null=False
    )
    address = models.ForeignKey(
        Address, on_delete=models.PROTECT, blank=False, null=False
    )
    contact_info = models.ForeignKey(
        ContactInfo, on_delete=models.PROTECT, blank=False, null=False
    )
    customer_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        unique=True,
        help_text="Old Accounting System's Customer ID",
    )
    customer_adjustment_in_percentage = models.IntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(BaseAbstractModel):
    """Represents a person associated with a company."""

    company = models.ForeignKey(
        ContactInfo,
        on_delete=models.CASCADE,
        blank=False,
        related_name="company_persons",
    )
    name = models.CharField(max_length=255, blank=False)
    title = models.CharField(max_length=255, blank=True)
    gender = models.PositiveSmallIntegerField(
        choices=GenderChoices.choices, default=GenderChoices.MALE
    )
    contact_info = models.ForeignKey(
        ContactInfo,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="contact_info_persons",
    )

    class Meta:
        ordering = ["company", "name"]

    def __str__(self):
        return self.company.name + ", " + self.name


class Profile(BaseAbstractModel):
    """Represents a user profile with additional information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    customer = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="customer_profile",
    )
    tech = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tech_profile",
    )
    title = models.CharField(max_length=30, null=True, blank=True)
    employment_id = models.CharField(max_length=10, null=True, blank=True)
    contact_info = models.ForeignKey(
        ContactInfo,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="contact_info_profiles",
    )
    photo = models.FileField(upload_to="uploads/users/profiles", null=True, blank=True)
    wallpaper = models.FileField(
        upload_to="uploads/users/wallpapers", null=True, blank=True
    )
    e_sign = models.FileField(upload_to="uploads/users/signs", null=True, blank=True)
    stamp = models.FileField(upload_to="uploads/users/stamps", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="location_profiles",
    )
    birth_date = models.DateField(null=True, blank=True)
    # Critical User Information
    email_confirmed = models.BooleanField(default=False)
    user_type = models.PositiveSmallIntegerField(
        choices=UserTypeChoices.choices, default=UserTypeChoices.CUSTOMER
    )
    worker_status = models.PositiveSmallIntegerField(
        choices=WorkerStatusChoices.choices, blank=True, null=True
    )
    id_number = models.PositiveIntegerField(blank=True, null=True, unique=True)
    physical_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="physical_address_profiles",
    )
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="billing_address_profiles",
    )
    interest_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text="exclusive for sub contractors.",
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="exclusive for sub contractors.",
    )

    def __str__(self):
        return self.user.email


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class CreditCard(BaseAbstractModel):
    user_profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=False, null=False
    )
    card_nickname = models.CharField(max_length=50, blank=False, null=False)
    name_on_the_card = models.CharField(max_length=255, blank=False, null=False)
    card_number = models.CharField(max_length=16, validators=[MinLengthValidator(16)])
    card_expiration_date = CardExpiryField()
    default_card = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        Address, on_delete=models.PROTECT, blank=False, null=False
    )

    def __str__(self):
        return str(self.user_profile.user) + " at " + str(self.card_nickname)


class BusinessCheckingAccount(BaseAbstractModel):
    user_profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=False, null=False
    )
    name_of_account = models.CharField(max_length=50, blank=False, null=False)
    bank_routing_number = models.CharField(
        max_length=9, validators=[MinLengthValidator(9)]
    )
    account_number = models.CharField(
        max_length=17, validators=[MinLengthValidator(17)]
    )
    business_tax_id = models.CharField(max_length=9, validators=[MinLengthValidator(9)])

    def __str__(self):
        return str(self.user_profile.user) + " at " + str(self.name_of_account)


class Project(BaseAbstractModel):
    name = models.CharField(
        max_length=255,
        blank=False,
        help_text="(/ : ?) characters are not allowed on project name",
    )
    address = models.ForeignKey(
        Address, on_delete=models.PROTECT, blank=False, null=False
    )
    contact_info = models.ForeignKey(
        ContactInfo, on_delete=models.PROTECT, blank=False, null=False
    )
    note = models.TextField(max_length=500, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(BaseAbstractModel):
    name = models.CharField(max_length=100, blank=False)
    priority = models.IntegerField(blank=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class LicenseInfo(BaseAbstractModel):
    key = models.CharField(max_length=255, blank=False, null=False, unique=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.key


class LicenseFiles(BaseAbstractModel):
    key = models.CharField(max_length=255, blank=False, unique=True, editable=True)
    value = models.FileField(upload_to="uploads/")

    class Meta:
        verbose_name = "License Information Files"
        verbose_name_plural = "License Information Files"

    def __str__(self):
        return self.key


class CompanySubmittalForm(BaseAbstractModel):
    form_name = models.CharField(max_length=255, blank=True)
    form_file = models.FileField(upload_to="uploads/submittalforms")
    related_services = models.ManyToManyField(Service, blank=False)

    def __str__(self):
        return self.form_name


class EmailBodyTemplate(BaseAbstractModel):
    name = models.CharField(max_length=255, blank=False, unique=True)
    content = HTMLField(
        null=True,
        blank=True,
        help_text="<b>Current User Information:</b><br />"
        "[user_name]: Logged in user Name | "
        "[user_title]: Logged in user Title | "
        "[user_cel]: Logged in user Cellphone Number | "
        "[user_tel]: Logged in user Telephone Number"
        "<br /><b>Customer Information:</b><br />"
        "[customer_company_name]: Customer Company Name | "
        "[customer_contact_person]: Customer Contact Person | "
        "[customer_email]: Customer Email | "
        "[customer_address_line_1]: Customer Address 2 | "
        "[customer_address_line_2]: Customer Address 1 | "
        "[customer_city]: Customer City | "
        "[customer_state]: Customer State | "
        "[customer_zip]: Customer Zip"
        "<br /><b>Insurance Company Information:</b><br />"
        "[ic_company_name]: Insurance Company Name | "
        "[ic_contact_name]: Insurance Company Contact Name | "
        "[ic_mail]: Insurance Company Email | "
        "[ic_tel]: Insurance Company Telephone | "
        "[ic_fax]: Insurance Company Fax | "
        "[ic_web]: Insurance Company Website | "
        "[ic_address_line_1]: Insurance Company Address 1 | "
        "[ic_address_line_2]: Insurance Company Address 2 | "
        "[ic_city]: Insurance Company City | "
        "[ic_state]: Insurance Company State | "
        "[ic_zip]: Insurance Company Zip",
    )

    class Meta:
        verbose_name = "Email Body Template"
        verbose_name_plural = "Email Body Template"

    def __str__(self):
        return self.name


class ModulesToEmailTemplateRelation(BaseAbstractModel):
    template = models.ForeignKey(
        EmailBodyTemplate, on_delete=models.PROTECT, blank=False
    )
    modules_list = (
        (1, "Estimate"),
        (2, "Quotation"),
        (3, "Proposal"),
        (4, "Invoice"),
        (5, "Email Footer"),
        (6, "COI"),
        (7, "Submittal"),
        (8, "Settlement"),
        (9, "Account Summary"),
    )
    module = models.PositiveSmallIntegerField(
        choices=modules_list, unique=True, blank=False
    )

    class Meta:
        verbose_name = "Connect Modules to Email Templates"
        verbose_name_plural = "Connect Modules to Email Templates"

    def __str__(self):
        return self.get_module_display()


class Setting(BaseAbstractModel):
    key = models.CharField(max_length=255, blank=False, unique=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    def __str__(self):
        return self.key


class TechLabelModel(BaseAbstractModel):
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)
    model_no = models.CharField(max_length=50, null=False, blank=False, unique=True)
    size = models.CharField(
        max_length=50, null=False, blank=False, unique=True, verbose_name="Size (in)"
    )

    def __str__(self):
        return self.name

from django.contrib.auth.models import User
from rest_framework import serializers

from mysite import settings
from mysite.core.models import ContactInfo, Person, Project, Company, Address, Profile, CreditCard
from mysite.s3_file_manager import S3


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = '__all__'


class CompanyCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = [
            "name",
            "tel",
            "fax",
            "mail",
            "web",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "zip",
            "company_type",
        ]


class CompanyEngineerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = [
            'id',
            'name',
            'tel',
            'fax',
            'mail',
            'web',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'zip',
            'company_type',
            'created_by'
        ]


class PersonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Person model.
    """
    contact_info = ContactInfoSerializer()

    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            'contact_info',
            "created_by",
        ]

    def create(self, validated_data):
        contact_info_data = validated_data.pop('contact_info')
        # Create the related ContactInfo object
        contact_info = ContactInfo.objects.create(**contact_info_data)
        # Now create the Person object and associate the created ContactInfo
        person = Person.objects.create(contact_info=contact_info, **validated_data)
        return person


class ProjectSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    contact_info = ContactInfoSerializer()

    class Meta:
        model = Project
        fields = [
            "name",
            "address",
            "contact_info",
            "note",
            "created_by"
        ]

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        contact_info_data = validated_data.pop('contact_info')

        # Create the related Address and ContactInfo objects
        address = Address.objects.create(**address_data)
        contact_info = ContactInfo.objects.create(**contact_info_data)

        # Now create the Project object
        project = Project.objects.create(address=address, contact_info=contact_info, **validated_data)

        return project


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for the Company model."""

    class Meta:
        model = Company
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model.
    Handles nested relationships for related models and file validations.
    """
    user = serializers.StringRelatedField(read_only=True)
    customer = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all(), required=False)
    tech = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all(), required=False)
    contact_info = serializers.PrimaryKeyRelatedField(queryset=ContactInfo.objects.all(), required=False)
    location = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), required=False)
    physical_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), required=False)
    billing_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), required=False)

    # Generated URLs for file fields
    photo_url = serializers.SerializerMethodField()
    e_sign_url = serializers.SerializerMethodField()
    stamp_url = serializers.SerializerMethodField()
    wallpaper_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id", "user", "customer", "tech", "title", "employment_id", "contact_info",
            "photo", "wallpaper", "e_sign", "stamp", "bio", "location", "birth_date",
            "email_confirmed", "user_type", "worker_status", "id_number", "physical_address",
            "billing_address", "interest_percentage", "hourly_rate", "photo_url", "e_sign_url",
        ]

    # File validation
    def validate_file_size(self, value):
        """
        Validates that the file size does not exceed the limit specified in settings.
        """
        if value.size > settings.LIMIT_FILE_SIZE:
            raise serializers.ValidationError("File size must not exceed 5MB.")
        return value

    def validate_photo(self, value):
        """
        Validates the photo file size.
        """
        return self.validate_file_size(value)

    def validate_e_sign(self, value):
        """
        Validates the e-sign file size.
        """
        return self.validate_file_size(value)

    def validate_stamp(self, value):
        """
        Validates the stamp file size.
        """
        return self.validate_file_size(value)

    def validate_wallpaper(self, value):
        """
        Validates the wallpaper file size.
        """
        return self.validate_file_size(value)

    # File URL generation
    def get_file_url(self, obj, field_name):
        """
        Generates the URL for a given file field (photo, e_sign, stamp, wallpaper).
        Utilizes S3 for fetching the file URL.
        """
        file_field = getattr(obj, field_name, None)
        if file_field:
            s3 = S3()
            return s3.get_bucket_object(file_field)
        return None

    def get_photo_url(self, obj):
        """
        Generates the URL for the photo file.
        """
        return self.get_file_url(obj, 'photo')

    def get_e_sign_url(self, obj):
        """
        Generates the URL for the e-sign file.
        """
        return self.get_file_url(obj, 'e_sign')

    def get_stamp_url(self, obj):
        """
        Generates the URL for the stamp file.
        """
        return self.get_file_url(obj, 'stamp')

    def get_wallpaper_url(self, obj):
        """
        Generates the URL for the wallpaper file.
        """
        return self.get_file_url(obj, 'wallpaper')


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = '__all__'

    def validate_default_card(self, value):
        # If value is True (indicating the card is being set as default)
        if value:
            # Get user_profile from either the instance (update case) or input data (create case)
            user_profile = self.instance.user_profile if self.instance else self.initial_data.get('user_profile')

            if not user_profile:
                raise serializers.ValidationError("User profile is required.")

            # Check if another default card exists for this user
            if CreditCard.objects.filter(user_profile=user_profile, default_card=True).exclude(
                    id=self.instance.id if self.instance else None).exists():
                raise serializers.ValidationError('User can only have one default card.')

        return value


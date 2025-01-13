from rest_framework import serializers
from django.contrib.auth import get_user_model

from mysite import settings
from mysite.core.models import (
    ContactInfo,
    Person,
    Project,
    Company,
    Address,
    Profile,
    CreditCard,
    LicenseFiles,
    CompanyType,
    Service,
)
from mysite.equipments.api.serializers import EquipmentSerializer
from mysite.s3_file_manager import S3

User = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    """Custom base serializer to exclude fields and set created_by automatically."""

    class Meta:
        abstract = True  # Make this class abstract so it won't be used directly

    def __init__(self, *args, **kwargs):
        # Remove 'archive' from the fields of the serializer dynamically
        exclude_fields = ["archive", "created_by"]
        super().__init__(*args, **kwargs)

        # Dynamically exclude 'archive' and 'created_by' from fields
        for field_name in exclude_fields:
            if field_name in self.fields:
                del self.fields[field_name]

    def create(self, validated_data):
        """Override create method to set 'created_by' automatically."""
        user = self.context["request"].user  # Get the user from the request context
        validated_data["created_by"] = user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Override update method to set 'created_by' automatically."""
        user = self.context["request"].user  # Get the user from the request context
        validated_data["created_by"] = user

        return super().update(instance, validated_data)


class AddressSerializer(BaseSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class ContactInfoSerializer(BaseSerializer):
    class Meta:
        model = ContactInfo
        fields = "__all__"


class CustomerSerializer(BaseSerializer):
    class Meta:
        model = Person
        fields = [
            "name",
            "company_type",
            "contact_info",
            "address",
            "customer_id",
            "customer_adjustment_in_percentage",
        ]


class PersonSerializer(BaseSerializer):
    """
    Serializer for the Person model.
    """

    contact_info = ContactInfoSerializer()

    class Meta:
        model = Person
        fields = "__all__"

    def create(self, validated_data):
        contact_info_data = validated_data.pop("contact_info")
        # Create the related ContactInfo object
        contact_info = ContactInfo.objects.create(**contact_info_data)
        # Now create the Person object and associate the created ContactInfo
        person = Person.objects.create(**validated_data, contact_info=contact_info)
        return person


class ProjectSerializer(BaseSerializer):
    address = AddressSerializer()
    contact_info = ContactInfoSerializer()

    class Meta:
        model = Project
        fields = ["id", "name", "address", "contact_info", "note", "created_by"]

    def create(self, validated_data):
        address_data = validated_data.pop("address")
        contact_info_data = validated_data.pop("contact_info")

        # Create the related Address and ContactInfo objects
        address = Address.objects.create(**address_data)
        contact_info = ContactInfo.objects.create(**contact_info_data)

        # Now create the Project object
        project = Project.objects.create(
            address=address, contact_info=contact_info, **validated_data
        )

        return project


class CompanySerializer(BaseSerializer):
    """Serializer for the Company model."""

    address = AddressSerializer()
    contact_info = ContactInfoSerializer()

    class Meta:
        model = Company
        fields = "__all__"

    def create(self, validated_data):
        """
        Override the create method to handle writable nested fields
        for the related models (Address and ContactInfo).
        """
        # Pop out the nested fields from validated_data
        address_data = validated_data.pop("address")
        contact_info_data = validated_data.pop("contact_info")

        # Create the related Address and ContactInfo instances
        address = Address.objects.create(**address_data)
        contact_info = ContactInfo.objects.create(**contact_info_data)

        validated_data["address"] = address
        validated_data["contact_info"] = contact_info

        # Create the Company instance
        company = Company.objects.create(**validated_data)

        return company

    def update(self, instance, validated_data):
        """
        Override the update method to handle updating nested fields.
        """
        # Pop out the nested fields from validated_data
        address_data = validated_data.pop("address", None)
        contact_info_data = validated_data.pop("contact_info", None)

        # Update related models (Address and ContactInfo)
        if address_data:
            for attr, value in address_data.items():
                setattr(instance.address, attr, value)
            instance.address.save()

        if contact_info_data:
            for attr, value in contact_info_data.items():
                setattr(instance.contact_info, attr, value)
            instance.contact_info.save()

        # Update the Company instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class UserSerializer(BaseSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()
        return user


class ProfileSerializer(BaseSerializer):
    """
    Serializer for the Profile model.
    Handles nested relationships for related models and file validations.
    """

    user = UserSerializer()
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), required=False
    )
    tech = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), required=False
    )
    contact_info = serializers.PrimaryKeyRelatedField(
        queryset=ContactInfo.objects.all(), required=False
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), required=False
    )
    physical_address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), required=False
    )
    billing_address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), required=False
    )

    # Generated URLs for file fields
    photo_url = serializers.SerializerMethodField()
    e_sign_url = serializers.SerializerMethodField()
    wallpaper_url = serializers.SerializerMethodField()

    user_type_title = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "customer",
            "tech",
            "title",
            "employment_id",
            "contact_info",
            "photo",
            "wallpaper",
            "wallpaper_url",
            "e_sign_url",
            "photo_url",
            "e_sign",
            "stamp",
            "bio",
            "location",
            "birth_date",
            "email_confirmed",
            "user_type",
            "user_type_title",
            "worker_status",
            "id_number",
            "physical_address",
            "billing_address",
            "interest_percentage",
            "hourly_rate",
            "photo_url",
            "e_sign_url",
        ]

    def get_user_type_title(self, obj):
        # Use Django's `get_FOO_display` to retrieve the title
        return obj.get_user_type_display()

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
        return self.get_file_url(obj, "photo")

    def get_e_sign_url(self, obj):
        """
        Generates the URL for the e-sign file.
        """
        return self.get_file_url(obj, "e_sign")

    def get_wallpaper_url(self, obj):
        """
        Generates the URL for the wallpaper file.
        """
        return self.get_file_url(obj, "wallpaper")


class CreditCardSerializer(BaseSerializer):
    class Meta:
        model = CreditCard
        fields = "__all__"

    def validate_default_card(self, value):
        # If value is True (indicating the card is being set as default)
        if value:
            # Get user_profile from either the instance (update case) or input data (create case)
            user_profile = (
                self.instance.user_profile
                if self.instance
                else self.initial_data.get("user_profile")
            )

            if not user_profile:
                raise serializers.ValidationError("User profile is required.")

            # Check if another default card exists for this user
            if (
                CreditCard.objects.filter(user_profile=user_profile, default_card=True)
                .exclude(id=self.instance.id if self.instance else None)
                .exists()
            ):
                raise serializers.ValidationError(
                    "User can only have one default card."
                )

        return value


class DocumentSerializer(BaseSerializer):
    class Meta:
        model = LicenseFiles
        fields = ["value"]


class CompanyTypeSerializer(BaseSerializer):
    class Meta:
        model = CompanyType
        fields = "__all__"


class ServiceSerializer(BaseSerializer):
    service_equipments = EquipmentSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = "__all__"

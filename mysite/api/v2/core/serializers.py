from rest_framework import serializers

from mysite.core.models import ContactInfo, Person, Project


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


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            "tel",
            "fax",
            "mail",
            "web",
            "created_by"
        ]


class EngineerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            "tel",
            "fax",
            "mail",
            "web",
            "created_by"
        ]


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            "company",
            "name",
            "title",
            "gender",
            "tel",
            "fax",
            "mail",
            "web",
            "created_by"
        ]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "name",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "zip",
            "tel",
            "fax",
            "mail",
            "note",
            "created_by"
        ]

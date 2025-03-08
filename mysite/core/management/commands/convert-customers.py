from django.core.management.base import BaseCommand
from django.db import connections
from mysite.core.models import (
    Company,
    Address,
    ContactInfo,
    CompanyType,
    GenderChoices,
    Person,
    User,
)


class Command(BaseCommand):
    help = "Convert old Person data from old database to new structure"

    def handle(self, *args, **options):
        self.stdout.write("Connecting to the old database...")

        old_cursor = connections["old_db"].cursor()
        old_cursor.execute(
            "SELECT core_person.id AS id, core_person.name AS name, core_person.title AS title, gender, core_person.tel AS tel, core_person.fax AS fax, core_person.mail AS mail, core_person.web AS web, core_contactinfo.name AS company_name FROM core_person INNER JOIN core_contactinfo ON core_contactinfo.id = core_person.company_id WHERE core_contactinfo.company_type_id=2; "
        )  # Modify table name as needed
        old_contacts = old_cursor.fetchall()

        for row in old_contacts:
            (
                id,
                name,
                title,
                gender,
                tel,
                fax,
                mail,
                web,
                company_name,
            ) = row

            # Create ContactInfo
            contact_info = ContactInfo.objects.create(
                tel=tel,
                fax=fax,
                mail=mail,
                web=web,
            )

            try:
                Person.objects.create(
                    name=name,
                    title=title,
                    gender=GenderChoices.MALE if gender == 1 else GenderChoices.FEMALE,
                    contact_info=contact_info,
                    company=Company.objects.filter(name__iexact=company_name).first(),
                )
            except:
                print(f"couldn't convert {name}")

            self.stdout.write(f"Converted: {name}")

        self.stdout.write("Data migration completed successfully.")

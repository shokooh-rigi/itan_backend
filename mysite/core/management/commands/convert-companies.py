from django.core.management.base import BaseCommand
from django.db import connections
from mysite.core.models import Company, Address, ContactInfo, CompanyType, User


class Command(BaseCommand):
    help = "Convert old ContactInfo data from old database to new structure"

    def handle(self, *args, **options):
        self.stdout.write("Connecting to the old database...")

        old_cursor = connections["old_db"].cursor()
        old_cursor.execute(
            "SELECT id, customer_id, name, tel, fax, mail, web, address_line_1, address_line_2, city, state, zip FROM core_contactinfo WHERE company_type_id=2"
        )  # Modify table name as needed
        old_contacts = old_cursor.fetchall()

        for row in old_contacts:
            (
                id,  # Assuming first column is ID
                customer_id,
                name,
                tel,
                fax,
                mail,
                web,
                address_line_1,
                address_line_2,
                city,
                state,
                zip_code,
            ) = row  # Adjust column order as needed

            # Create Address
            address = Address.objects.create(
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                city=city,
                state=state,
                zip=zip_code,
            )

            # Create ContactInfo
            contact_info = ContactInfo.objects.create(
                tel=tel,
                fax=fax,
                mail=mail,
                web=web,
            )

            # Create Company
            company_type = CompanyType.objects.get(
                name="MECHANICAL CONTRACTOR"
            )  # Ensure this exists

            Company.objects.create(
                name=name,
                company_type=company_type,
                address=address,
                contact_info=contact_info,
                customer_id=customer_id,
            )

            self.stdout.write(f"Converted: {name}")

        self.stdout.write("Data migration completed successfully.")

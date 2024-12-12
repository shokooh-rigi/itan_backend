import datetime
import os

from django.db import transaction

from mysite import settings
from mysite.core.models import LicenseInfo, LicenseFiles
from mysite.order.models import TechLabelExtraFields, TechLabel
from mysite.s3_file_manager import S3


class TechLabelServiceLayer:
    def __init__(self, user=None, data=None):
        self.user = user
        self.data = data

    @transaction.atomic
    def update_tech_label(self, tech_label, order):
        """
        Updates a TechLabel and its extra fields.
        """
        if not self.data:
            raise ValueError("Invalid data provided.")

        # Update or create TechLabel
        if tech_label:
            tech_label.order = self.data.get('order', tech_label.order)
        else:
            tech_label = TechLabel.objects.create(order=order)

        tech_label.save()

        # Clear and recreate extra fields
        TechLabelExtraFields.objects.filter(tech_label=tech_label).delete()
        extra_fields = self.data.get('extra_fields', [])
        for field in extra_fields:
            TechLabelExtraFields.objects.create(
                tech_label=tech_label,
                title=field['title'],
                content=field['content']
            )

        return tech_label

    def generate_pdf(self, tech_label, order):
        """
        Generate a PDF for the TechLabel and upload it to S3.
        """
        from platform import system
        file_name = 'techlabel-' + str(order.project_number) + '.pdf'
        file_path = os.path.join(settings.MEDIA_ROOT, 'pdfs', 'techlabel', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Prepare parameters
        parameters = {
            'datenow': datetime.datetime.now().date(),
            'file_name': 'techlabel-' + str(order.project_number),
            'tech_label': tech_label,
            'extra_fields': TechLabelExtraFields.objects.filter(tech_label=tech_label),
            'license_info': {
                'owner_name': LicenseInfo.objects.get(key='OwnerName').value,
                'owner_title': LicenseInfo.objects.get(key='OwnerTitle').value,
                'owner_logo': LicenseFiles.objects.get(key='OwnerLogo').value,
                'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
                'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
                'company_name': LicenseInfo.objects.get(key='CompanyName').value,
            },
            'WEB_URL': settings.WEB_URL,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL,
            'os': system(),
        }

        # Create the PDF
        techlabel_pdf = TechLabel.create_techlabel_pdf(parameters)
        with open(file_path, 'wb') as pdf_file:
            pdf_file.write(techlabel_pdf)

        # Upload to S3
        s3 = S3()
        try:
            s3.upload_file_to_bucket(key=file_path, file_name=f'media/pdfs/techlabel/{file_name}')
        except Exception as e:
            raise Exception(f"S3 upload failed: {e}")

        return file_path

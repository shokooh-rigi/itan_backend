import logging
import os
from typing import Dict
from typing import List

from django.conf import settings
from django.core.mail import BadHeaderError
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404

from mysite.core.models import LicenseInfo
from mysite.core.models import ModulesToEmailTemplateRelation
from mysite.gi.models import Invoice, InvoiceHistory
from mysite.s3_file_manager import S3

logger = logging.getLogger(__name__)


class InvoiceEmailService:
    """Service to manage invoice-related to email  operations."""

    def send_invoice_email(self, invoice_id: int, to_email: List[str], cc: List[str] = None, subject: str = "Invoice") -> bool:
        """Send an invoice email to the specified recipients.

        Args:
            invoice_id (int): ID of the invoice to be emailed.
            to_email (List[str]): List of recipient email addresses.
            cc (List[str]): List of CC email addresses.
            subject (str): Subject of the email.

        Returns:
            bool: True if the email is sent successfully, False otherwise.
        """
        try:
            # Fetch the latest invoice history
            latest_invoice_history = InvoiceHistory.objects.filter(invoice__id=invoice_id).order_by('id').last()
            if not latest_invoice_history:
                logger.error(f"No invoice history found for invoice ID {invoice_id}.")
                return False

            s3_key: str = f"{settings.STORAGE_INVOICE_PDFS_PATH}{latest_invoice_history.pdf_filename}.pdf"

            email_service = EmailService(
                model_id=invoice_id,
                model_name=Invoice,
                storage_service=S3(),
                s3_key=s3_key,
                modules_to_email_template=3,
                user=self._prepare_user_info(),
            )
            return email_service.send_email(
                to_email=to_email,
                cc=cc,
                subject=subject,
            )

        except Exception as e:
            logger.error(f"Failed to send invoice email for ID {invoice_id}: {e}")
            return False

    @staticmethod
    def _prepare_user_info():
        """Prepare user-related information for email footer content.

        Returns:
            Dict[str, str]: A dictionary containing user details for email templates.
        """
        user: dict = {
            "user_name": "TAB Technologies, INC. Operator",
            "user_title": "Estimator",
            "user_cell": "",
            "user_tel": f"{LicenseInfo.objects.get(key='OwnerTel').value} Office",
        }

        profile = getattr(settings, "REQUEST_USER_PROFILE", None)  # Assuming user profile is available in request
        if profile:
            user["user_name"] = f"{profile.first_name} {profile.last_name}".strip()
            user["user_title"] = profile.title or user["user_title"]
            user["user_cell"] = profile.cell or user["user_cell"]
            user["user_tel"] = profile.tel or user["user_tel"]

        return user


class EmailService:
    """Service to handle all email-related tasks.

    This service is responsible for composing and sending emails
     including attaching PDF documents.

    Attributes:
        model_id (Data Base Model Name): The name of model associated with the email.
        storage_service (StorageService): Service for handling PDF storage.
        body_content (str): The main content of the email body.
        footer_content (str): The footer content of the email body.
        attachment_path (str): The path to the attached PDF file.
    """

    def __init__(
            self,
            model_id: int,
            model_name,
            storage_service: S3,
            s3_key: str,
            modules_to_email_template: int,
            user: Dict = None,

    ):
        """Initialize EmailService with the specified model, storage service, and template service.

        Args:
            model_id (int): The ID of the related model to associate with this service.
            storage_service (S3): An instance of S3 storage service.
        """
        self.estimate = get_object_or_404(model_name, id=model_id)
        self.storage_service = storage_service
        self.s3_key = s3_key
        self.body_content = ""
        self.footer_content = ""
        self.attachment_path = ""
        self.modules_to_email_template = modules_to_email_template
        self.user = user

    def _fetch_body_content(self):
        """Fetch the body content of the email using the template service.

        Returns:
            str: The formatted body content for the email.
        """
        if ModulesToEmailTemplateRelation.objects.filter(module=self.modules_to_email_template).exists():
            invoice_content = ModulesToEmailTemplateRelation.objects.get(module=4).template.content
        else:
            invoice_content = "There was no email template defined for 'Invoice'."
        return invoice_content

    def _fetch_footer_content(self):
        """Fetch the footer content of the email using the template service.

        Returns:
            str: The formatted footer content for the email.
        """
        if ModulesToEmailTemplateRelation.objects.filter(module=5).exists():
            footer_content = ModulesToEmailTemplateRelation.objects.get(module=5).template.content
        else:
            footer_content = "There was no email template defined for 'Email Footer'."
        if self.user:
            return footer_content.format(
                user_name=self.user.get("user_name", ""),
                user_title=self.user.get("user_title", ""),
                user_cell=self.user.get("user_cell", ""),
                user_tel=self.user.get("user_tel", ""),
            )
        else:
            return footer_content

    def _fetch_pdf_attachment(self) -> str:
        """Fetch the PDF attachment for the model from the S3 storage service.

        This method retrieves the PDF file from the storage service and saves it locally.

        Returns:
            str: The local path of the saved PDF file.

        Raises:
            Exception: If there is an error while fetching or saving the PDF.
        """
        try:
            # Using S3's `get_bucket_object` to retrieve the PDF
            response_content = self.storage_service.get_bucket_object(key=self.s3_key)
            if response_content is None:
                raise FileNotFoundError(f"PDF file with key '{self.s3_key}' not found in S3 storage.")
            with open(self.s3_key, 'wb') as pdf_file:
                pdf_file.write(
                    response_content if isinstance(response_content, bytes) else response_content.encode('utf-8'))
            return self.s3_key

        except Exception as e:
            logger.error(f"Failed to fetch or save PDF attachment: {e}")
            raise

    def _prepare_email_message(
            self,
            to_email: List[str],
            cc: List[str],
            subject: str,
            message: str,
    ) -> EmailMessage:
        """Prepare the email message with the specified details.

        Args:
            to_email (List[str]): List of recipient email addresses.
            cc (List[str]): List of CC email addresses.
            subject (str): The subject of the email.
            message (str): The body content of the email.

        Returns:
            EmailMessage: The constructed email message object.

        Raises:
            Exception: If there is an error while attaching the PDF file.
        """
        email_msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_email,
            cc=cc,
        )
        email_msg.content_subtype = "html"

        try:
            self.attachment_path = self._fetch_pdf_attachment()
            email_msg.attach_file(self.attachment_path)
        except Exception as e:
            logger.error(f"Failed to attach PDF file: {e}")
            raise
        return email_msg

    def send_email(
            self,
            to_email: List[str],
            cc: List[str],
            subject: str,
    ) -> bool:
        """Send the email with the specified recipient, CC, and subject.

        Args:
            to_email (List[str]): List of recipient email addresses.
            cc (List[str]): List of CC email addresses.
            subject (str): The subject of the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.

        Logs errors if sending fails, including invalid headers and other exceptions.
        """
        try:
            self.body_content = self._fetch_body_content()
            self.footer_content = self._fetch_footer_content()
            message = f"{self.body_content}<br />{self.footer_content}"
            email_msg = self._prepare_email_message(
                to_email=to_email,
                cc=cc,
                subject=subject,
                message=message,
            )
            email_msg.send()
            os.remove(self.attachment_path)
            return True
        except BadHeaderError:
            logger.error("Invalid header found.")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
        finally:
            if os.path.exists(self.attachment_path):
                os.remove(self.attachment_path)

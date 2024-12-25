import logging
import os
from typing import List
from urllib.request import Request

from django.conf import settings
from django.core.mail import EmailMessage, BadHeaderError
from django.shortcuts import get_object_or_404

from mysite.core.models import ModulesToEmailTemplateRelation
from mysite.core.views import htmlbodytemplate_tag_converter
from mysite.estimator.models import Estimate
from mysite.estimator.templatetags.estimator_tags import pdf_filename_generator
from mysite.s3_file_manager import S3

logger = logging.getLogger(__name__)


class TemplateService:
    """Retrieves email templates based on module identifiers."""

    def get_template(self, module: int) -> str:
        """Fetch an email template based on the provided module ID.

        Args:
            module (int): The module identifier.

        Returns:
            str: The email template content or a fallback message if not found.
        """
        try:
            relation = get_object_or_404(
                ModulesToEmailTemplateRelation,
                module=module
            )
            return relation.template.content
        except Exception as e:
            logger.error(f"Error fetching template for module {module}: {e}")
            return "No email template defined for this module."


class EstimateEmailService:
    """Service to handle all email-related tasks for estimates.

    This service is responsible for composing and sending emails
    related to estimate, including attaching PDF documents.

    Attributes:
        estimate (Estimate): The estimate associated with the email.
        customer: The customer associated with the estimate.
        storage_service (StorageService): Service for handling PDF storage.
        template_service (TemplateService): Service for handling email templates.
        body_content (str): The main content of the email body.
        footer_content (str): The footer content of the email body.
        attachment_path (str): The path to the attached PDF file.
    """

    def __init__(
            self,
            request: Request,
            estimate_id: int,
            storage_service: S3,
            template_service: TemplateService,
            modules_to_email_template: int,
            pdf_path: str,
            pdf_prefix: str,

    ):
        """Initialize EstimateEmailService with the specified estimate, storage service, and template service.

        Args:
            estimate_id (int): The ID of the estimate to associate with this service.
            storage_service (S3): An instance of S3 storage service.
            template_service (TemplateService): An instance of a template service.
        """
        self.request = request
        self.estimate = get_object_or_404(Estimate, id=estimate_id, is_deleted=False)
        self.customer = self.estimate.customer
        self.storage_service = storage_service
        self.template_service = template_service
        self.body_content = ""
        self.footer_content = ""
        self.attachment_path = ""
        self.modules_to_email_template = modules_to_email_template
        self.pdf_path = pdf_path
        self.pdf_prefix = pdf_prefix

    def _fetch_body_content(self) -> str:
        """Fetch the body content of the email using the template service.

        Returns:
            str: The formatted body content for the email.
        """
        content = self.template_service.get_template(module=self.modules_to_email_template)
        # todo: check this view: htmlbodytemplate_tag_converter is good practise or not
        return htmlbodytemplate_tag_converter(
            form_type=1,
            content=content,
            request=self.request,
            customer=self.customer,
        )

    def _fetch_footer_content(self) -> str:
        """Fetch the footer content of the email using the template service.

        Returns:
            str: The formatted footer content for the email.
        """
        content = self.template_service.get_template(module=5)
        return htmlbodytemplate_tag_converter(
            form_type=1,
            content=content,
            request=self.request,
            customer=self.customer,
        )

    def _fetch_pdf_attachment(self) -> str:
        """Fetch the PDF attachment for the estimate from the S3 storage service.

        This method retrieves the PDF file from the storage service and saves it locally.

        Returns:
            str: The local path of the saved PDF file.

        Raises:
            Exception: If there is an error while fetching or saving the PDF.
        """
        pdf_filename_generate = pdf_filename_generator(self.estimate.id, self.pdf_prefix)
        pdf_filename = f"{settings.MEDIA_ROOT}{self.pdf_path}{pdf_filename_generate}.pdf"
        s3_key = f"{settings.STORAGE_ESTIMATE_PDFS_PATH}{pdf_filename}"

        try:
            # Using S3's `get_bucket_object` to retrieve the PDF
            response_content = self.storage_service.get_bucket_object(key=s3_key)
            if response_content is None:
                raise FileNotFoundError(f"PDF file with key '{s3_key}' not found in S3 storage.")
            with open(pdf_filename, 'wb') as pdf_file:
                # todo :  check correctly write or not?
                pdf_file.write(
                    response_content if isinstance(response_content, bytes) else response_content.encode('utf-8'))
            return pdf_filename
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

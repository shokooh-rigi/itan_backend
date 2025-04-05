from custom_user.models import User


def send_announcement_email_task(announcement):
    """
    Task to send an announcement email.
    """
    from django.core.mail import send_mail
    from django.conf import settings

    env = env

    subject = f"New Announcement: {announcement.title}"
    message = f"Hello,\n\nWe have a new announcement on {settings.SYSTEM_NAME} for you:\n\n{announcement.content}\n\nBest regards,\nYour Team"
    recipient_list = [user.email for user in User.objects.all() if user.is_staff]

    # Send the email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )

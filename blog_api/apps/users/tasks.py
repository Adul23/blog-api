import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email(self, user_id: int):
    """
    Send a welcome email to a newly registered user.

    Automatic retries are important here because email delivery depends
    on external SMTP servers that may be temporarily unavailable.
    Without retries, a new user would never receive their welcome email
    if the mail server hiccups during registration.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user = User.objects.get(id=user_id)
    send_mail(
        subject="Welcome to the Blog!",
        message=f"Hi {user.first_name},\n\nWelcome to our blog platform!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info("Welcome email sent to %s.", user.email)

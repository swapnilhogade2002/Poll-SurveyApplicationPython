from django.test import TestCase

# Create your tests here.
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test email.',
    settings.DEFAULT_FROM_EMAIL,
    ['recipient@example.com'],
    fail_silently=False,
)

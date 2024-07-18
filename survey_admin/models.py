from django.db import models
from django.contrib.auth.models import AbstractUser
import pyotp
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid


class CustomUser(AbstractUser):
    class CustomUserState(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'

    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=63, choices=ROLE_CHOICES, default='user')
    state = models.CharField(max_length=63, choices=CustomUserState.choices, default=CustomUserState.PENDING)
    is_receive_emails = models.BooleanField(default=True)
    mfa_secret_key = models.CharField(max_length=50, null=True)
    mfa_enabled = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:  
            self.mfa_secret_key = pyotp.random_base32()
        super().save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'users'

# for survey models
class Survey(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class Question(models.Model):
    TEXT = 'text'
    RADIO = 'radio'
    SELECT = 'select'
    INTEGER = 'integer'
    RATING = 'rating'
    QUESTION_TYPES = [
        (TEXT, 'Text'),
        (RADIO, 'Radio'),
        (SELECT, 'Select'),
        (INTEGER, 'Integer'),
        (RATING, 'Rating'),
    ]

    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(max_length=200)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default=TEXT)
    created_by = models.ForeignKey(CustomUser, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.question_text

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)

    def __str__(self):
        return self.choice_text

class Response(models.Model):
    survey = models.ForeignKey(Survey, related_name='responses', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='responses', on_delete=models.CASCADE, null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.is_anonymous:
            return f"Anonymous response to {self.survey.title} at {self.created_at}"
        else:
            return f"Response to {self.survey.title} by {self.user.username} at {self.created_at}"

class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True, null=True)
    choice_answer = models.ForeignKey(Choice, blank=True, null=True, on_delete=models.CASCADE)
    integer_answer = models.IntegerField(blank=True, null=True)
    rating_answer = models.IntegerField(blank=True, null=True)


    def __str__(self):
        if self.response.is_anonymous:
            return f"Anonymous answer to {self.question.question_text}"
        else:
            return f"Answer to {self.question.question_text} by {self.response.user.username}"


class PublicSurveyLink(models.Model):
    survey = models.OneToOneField(Survey, related_name='public_link', on_delete=models.CASCADE)
    link_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PrivateSurveyLink(models.Model):
    survey = models.ForeignKey(Survey, related_name='private_links', on_delete=models.CASCADE)
    respondent_email = models.EmailField()
    link_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
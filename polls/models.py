from django.db import models

# Create your models here.
from django.utils import timezone
from django.db import models
from survey_admin.models import CustomUser

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published',default= timezone.now)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_questions', null=True, default=None)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
    def __str__(self):
        return self.choice_text
        
class Vote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    vote_date = models.DateTimeField(default=timezone.now)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username} voted on {self.question.question_text}"
        else:
            return f"Anonymous vote on {self.question.question_text}"

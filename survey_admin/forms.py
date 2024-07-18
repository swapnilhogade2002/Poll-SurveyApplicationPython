# forms.py
# from django import forms
# from .models import Survey
# from .models import Question, Choice

# class SurveyForm(forms.ModelForm):
#     class Meta:
#         model = Survey
#         fields = ['title', 'description']

# class QuestionForm(forms.ModelForm):
#     class Meta:
#         model = Question
#         fields = ['question_text', 'question_type']

# class ChoiceForm(forms.ModelForm):
#     class Meta:
#         model = Choice
#         fields = ['choice_text']

# survey_admin/forms.py

from django import forms
from .models import CustomUser
from django.core.validators import RegexValidator

# admin/forms.py 

from django import forms
from polls.models import Question,Choice
from django.forms import inlineformset_factory

class CustomUserForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9]*$',
                message='Username must be alphanumeric and contain no spaces.',
            ),
        ],
        error_messages={
            'required': 'Username is required.',
            'unique': 'A user with that username already exists.',
        },
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'is_receive_emails', 'mfa_enabled', 'is_deleted']
        labels = {
            'username': 'Username',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'role': 'Role',
            'is_receive_emails': 'Receive Emails',
            'mfa_enabled': 'MFA Enabled',
            'is_deleted': 'Is Deleted',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_receive_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mfa_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_deleted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }





class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'pub_date' ,'start_time', 'end_time']

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['pub_date'].widget.attrs['readonly'] = True


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', 'votes']

ChoiceFormSet = inlineformset_factory(Question, Choice, form=ChoiceForm, extra=1, can_delete=True)

# surveys


from .models import Survey, Question, Choice
from .models import Question as SurveyQuestion, Choice as SurveyChoice
from django.forms import inlineformset_factory

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description', 'start_time', 'end_time']

class SurveyQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text']


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text']




class SurveyChoiceForm(forms.ModelForm):
     class Meta:
        model = Choice
        fields = ['choice_text']
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control'}),

        }

SurveyQuestionFormSet = inlineformset_factory(Survey, SurveyQuestion, form=SurveyQuestionForm, extra=1, can_delete=True)
SurveyChoiceFormSet = inlineformset_factory(SurveyQuestion, Choice, form=SurveyChoiceForm, extra=1)

class AnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey')
        super(AnswerForm, self).__init__(*args, **kwargs)

        for question in survey.questions.all():
            if question.question_type == Question.TEXT:
                self.fields[f'text_answer_{question.id}'] = forms.CharField(label=question.question_text, required=True)
            elif question.question_type == Question.RADIO:
                choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                self.fields[f'choice_answer_{question.id}'] = forms.ChoiceField(label=question.question_text, choices=choices, widget=forms.RadioSelect, required=True)
            elif question.question_type == Question.SELECT:
                choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                self.fields[f'choice_answer_{question.id}'] = forms.ChoiceField(label=question.question_text, choices=choices, required=True)
            elif question.question_type == Question.INTEGER:
                self.fields[f'integer_answer_{question.id}'] = forms.IntegerField(label=question.question_text, required=True)
            elif question.question_type == Question.RATING:
                self.fields[f'integer_answer_{question.id}'] = forms.IntegerField(label=question.question_text, required=True)

        self.fields['is_anonymous'] = forms.BooleanField(label='Answer Anonymously', required=False)

# manage profile
from django.contrib.auth import get_user_model

CustomUser = get_user_model()
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
        error_messages={
            'required': 'First name is required.'
        }
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
        error_messages={
            'required': 'Last name is required.'
        }
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'}),
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Enter a valid email address.'
        }
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
           
        }
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'is_receive_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mfa_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


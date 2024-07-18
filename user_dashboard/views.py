from django.shortcuts import render
import pyotp
from pyotp import TOTP, random_base32 as pyotp_secret
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
import qrcode
from django.http import HttpResponseForbidden, JsonResponse
from io import BytesIO
from django.http import HttpResponse
import pyotp
from pyotp import TOTP, random_base32 as pyotp_secret
import base64
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, get_object_or_404, redirect
from polls.models import Question, Choice , Vote
from .forms import QuestionForm, ChoiceForm,SurveyChoiceForm
from django.forms import inlineformset_factory
from django.utils import timezone
from .forms import QuestionForm, ChoiceForm
from django.shortcuts import redirect
from django.contrib.auth import logout
from survey_admin.models import Survey,  Question as SurveyQuestion  ,  Choice as SurveyChoice , Answer, Response, CustomUser
from .forms import SurveyForm, SurveyQuestionForm, SurveyChoiceForm
from .forms import AnswerForm
from .forms import SurveyForm, SurveyQuestionFormSet, SurveyChoiceFormSet
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from django.shortcuts import render
from django.conf import settings
from survey_admin.models import Survey, Answer as  SurveyAnswer, Question as SurveyQuestion ,CustomUser, PublicSurveyLink, PrivateSurveyLink
import csv
from django.core.mail import send_mail
from .forms import UserProfileForm

def user_logout(request):
    """
    Logs out the current user and redirects to the admin login page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the '/admin-login' URL after logging out the user.
    """
    try:
        logout(request)
        return redirect('/admin-login')
    except Exception as e:
        return render(request, 'error.html', {'error_message': f'Error logging out: {str(e)}'})

def user_dashboard(request):
    """
    Renders the user dashboard with information about MFA status, username, polls count, and surveys count.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template 'user_dashboard.html' with context data.
    """
    try:
        mfa_enabled = request.user.mfa_enabled  
        username = request.user.username
        user_polls_count = Question.objects.filter(created_by=request.user).count()
        user_surveys_count = Survey.objects.filter(created_by=request.user).count()

        context = {
            'mfa_enabled': mfa_enabled,
            'username':username,
            'user_polls_count':user_polls_count,
            'user_surveys_count':user_surveys_count,

        }
        return render(request, 'user_dashboard.html' ,context)
    except Exception as e:
        return render(request, 'error.html', {'error_message': f'Error fetching dashboard data: {str(e)}'})

# QR code generation and verfication of OTP for MFA -start
def generate_qr_code(request):
    """
    Generates a QR code for two-factor authentication (2FA) using the user's MFA secret key.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template 'qr_code.html' with the QR code image as base64 encoded string.
                      Returns HttpResponse with message "MFA secret key not found." if the key is missing.
    """
    try:
        mfa_secret_key = request.user.mfa_secret_key
        otpauth_url = TOTP(mfa_secret_key).provisioning_uri(request.user.email, issuer_name="admin_portal")

        if mfa_secret_key:
            # Generate OTP using pyotp
            totp = pyotp.TOTP(str(mfa_secret_key))
            otp = totp.now()

            # Generate the QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(otpauth_url)
            img = qrcode.make(otpauth_url)
            qr.make(fit=True)

            # Create an in-memory stream to save the QR code image
            qr_code_image = BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(qr_code_image, format="PNG")
            qr_code_image.seek(0)

            # Encode the image as base64
            qr_code_image_base64 = base64.b64encode(qr_code_image.getvalue()).decode()

            # Pass the QR code image and OTP to the template for rendering
            return render(request, 'qr_code.html', {'qr_code_image': qr_code_image_base64})
        else:
            return HttpResponse("MFA secret key not found.")
    except Exception as e:
        return HttpResponse(f"Error generating QR code: {str(e)}")

@login_required
def user_disable_mfa(request):
    """
    Disables Multi-Factor Authentication (MFA) for the current logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the user dashboard with a success message upon successful disabling of MFA.
    """
    try:
        if request.method == 'POST':
            request.user.mfa_enabled = False
            request.user.save()
            messages.success(request, 'Multi-Factor Authentication has been disabled.')
            return redirect('user_dashboard') 
    except Exception as e:
        messages.error(request, f"Failed to disable Multi-Factor Authentication: {str(e)}")
    return redirect('user_dashboard')


# users manageing polls-start
@login_required
def user_poll_list(request):
    """
    Renders a list of polls created by the current logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template with the user's polls.
    """
    try:
        polls = Question.objects.filter(created_by=request.user).prefetch_related('choice_set')
        return render(request, 'user_poll_list.html', {'polls': polls})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while retrieving your polls.'})


# working add option when creating polls
@login_required
def user_poll_create(request):
    """
    Handles the creation of a new poll by the logged-in user.

    On POST request:
    - Validates and saves a new question with associated choices.
    - Redirects to 'user_poll_list' upon successful creation.

    On GET request:
    - Renders the 'user_poll_create.html' template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template or redirection based on request method and validation.
    """
    try: 
        if request.method == 'POST':
            question_text = request.POST.get('question_text')
            start_time = request.POST.get('start_time')  
            end_time = request.POST.get('end_time')  
            if not question_text:
                return render(request, 'user_poll_create.html', {'error_message': 'Question text is required.'})

            # Create the question object
            question = Question.objects.create(question_text=question_text, created_by=request.user, 
            pub_date=timezone.now(), start_time=start_time,
            end_time=end_time)

            # Process choices
            choice_texts = request.POST.getlist('choice_text')
            if not choice_texts or len(choice_texts) < 2:
                question.delete()  
                return render(request, 'user_poll_create.html', {'error_message': 'At least two choices are required.'})

            # Create choices for the question
            for choice_text in choice_texts:
                Choice.objects.create(question=question, choice_text=choice_text)

            return redirect('user_poll_list')  

        return render(request, 'user_poll_create.html')
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while creating your poll.'})


@login_required
def user_poll_detail(request, poll_id):
    """
    Renders the details of a specific poll for the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        poll_id (int): The ID of the poll to display.

    Returns:
        HttpResponse: Rendered template displaying the poll details.
    """
    try: 
        poll = get_object_or_404(Question, pk=poll_id)
        return render(request, 'user_poll_detail.html', {'poll': poll})
    except Question.DoesNotExist:
        return render(request, 'error.html', {'error_message': 'Poll not found.'})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while fetching poll details.'})


@login_required
def user_poll_update(request, poll_id):
    """
    Handles updating a poll and its choices for the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        poll_id (int): The ID of the poll to update.

    Returns:
        HttpResponse: Redirects to the updated poll detail page on success, or renders the update form with errors on failure.
    """
    try: 
        poll = get_object_or_404(Question, pk=poll_id) 
        
        ChoiceFormSet = inlineformset_factory(Question, Choice, form=ChoiceForm, extra=1, can_delete=True)
        if request.method == 'POST':
            form = QuestionForm(request.POST, instance=poll)
            formset = ChoiceFormSet(request.POST, instance=poll)
    
            if form.is_valid() and formset.is_valid():
                form.save()
                formset.save()  
    
                return redirect('user_poll_detail', poll_id=poll.id)
            else:
               pass
        else:
            form = QuestionForm(instance=poll)
            formset = ChoiceFormSet(instance=poll)
        
        return render(request, 'user_poll_update.html', {'form': form, 'formset': formset})
    except Question.DoesNotExist:
        return render(request, 'error.html', {'error_message': 'Poll not found.'})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while updating the poll.'})


@login_required
def user_poll_delete(request, poll_id):
    """
    Handles the deletion of a poll by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        poll_id (int): The ID of the poll to delete.

    Returns:
        HttpResponse: Redirects to the user's poll list page after deleting the poll, or renders a confirmation page before deletion.
    """
    try: 
        poll = get_object_or_404(Question, pk=poll_id)
        if request.method == "POST":
            poll.delete()
            return redirect('user_poll_list')
        return render(request, 'user_poll_confirm_delete.html', {'poll': poll})
     
    except Question.DoesNotExist:
        return render(request, 'error.html', {'error_message': 'Poll not found.'})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while deleting the poll.'})


@login_required
def user_polls_graph(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
        votes = question.choice_set.all()

        votedata = [{'choice_text': choice.choice_text, 'votes': choice.votes} for choice in votes]

        context = {
            'question': question,
            'votedata': votedata,
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'votedata': votedata}, safe=False)
        else:
            return render(request, 'user_poll_results.html', context)
    except Question.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Question not found'}, status=404)
        else:
            return render(request, 'error.html', {'message': 'Question not found'}, status=404)



@login_required
def user_dashboard_analytics(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    total_votes = Vote.objects.filter(question=question).count()

    # Calculate percentage distribution of votes
    choice_texts = []
    choice_votes = []
    choice_percentages = []

    if total_votes > 0:
        for choice in question.choice_set.all():
            choice_texts.append(choice.choice_text)
            choice_votes.append(choice.votes)
            choice_percentages.append(round((choice.votes / total_votes) * 100, 2))
    else:
        choice_percentages = [0] * question.choice_set.count()

    data = {
        'question_text': question.question_text,
        'total_votes': total_votes,
        'choice_texts': choice_texts,
        'choice_votes': choice_votes,
        'choice_percentages': choice_percentages,
    }

    return JsonResponse(data)
# users manageing polls-end


# users managing survey-start
@login_required
def user_survey_list(request):
    """
    Renders a list of surveys created by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'user_survey_list.html' template with a context containing the surveys created by the user.
    """
    try:
        surveys = Survey.objects.filter(created_by=request.user).distinct()
        return render(request, 'user_survey_list.html', {'surveys': surveys})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while fetching surveys.'})


@login_required
def user_survey_create(request):
    """
    Handles creation of a new survey by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'user_survey_create.html' template with a form to create a new survey.
                      If the form is submitted successfully, redirects to 'user_survey_list'.
                      If there are validation errors or missing data, renders the form again with appropriate error messages.
    """
    try: 
        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            if not title:
                return render(request, 'user_survey_create.html', {'error_message': 'Survey title is required.'})     
            survey = Survey.objects.create(title=title, description=description, created_by=request.user, start_time=start_time,end_time=end_time)
            return redirect('user_survey_list')  
        return render(request, 'user_survey_create.html')
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while creating the survey.'})


@login_required
def user_question_create(request, survey_id):
    """
    Handles creation of a new question for a survey by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to which the question belongs.

    Returns:
        HttpResponse: Renders the 'user_question_create.html' template with a form to create a new question.
                      If the form is submitted successfully, redirects to 'user_survey_list'.
                      If there are validation errors or missing data, renders the form again with appropriate error messages.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)

        if request.method == 'POST':
            question_text = request.POST.get('question_text')
            question_type = request.POST.get('question_type')
            
            if not question_text:
                return render(request, 'user_question_create.html', {'survey': survey, 'error_message': 'Question text is required.'})
            
            question = SurveyQuestion.objects.create(
                survey=survey,
                question_text=question_text,
                question_type=question_type,
                created_by=request.user
            )
            
            if question_type in [SurveyQuestion.RADIO, SurveyQuestion.SELECT]:
                choices = request.POST.getlist('choice_text')
                for choice_text in choices:
                    if choice_text:
                        SurveyChoice.objects.create(question=question, choice_text=choice_text)
            
            return redirect('user_survey_list') 
        
        return render(request, 'user_question_create.html', {'survey': survey})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while creating the question.'})

@login_required
def user_answer_survey(request, survey_id):
    """
    Handles answering a survey by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to be answered.

    Returns:
        HttpResponse: Renders the 'user_survey_answer.html' template with a form to answer the survey.
                      If the form is submitted successfully, redirects to 'user_survey_list'.
                      If there are validation errors or missing data, renders the form again with appropriate error messages.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)

        # Check if the user has already responded to the survey
        if request.user.is_authenticated:
            existing_response = Response.objects.filter(survey=survey, user=request.user).first()
        else:
            existing_response = None
            pass

        if existing_response:
            messages.error(request, "You have already responded to this survey!")
            return redirect('user_survey_list')

        if request.method == 'POST':
            form = AnswerForm(request.POST, survey=survey)

            if form.is_valid():
                if form.cleaned_data['is_anonymous']:
                    response = Response.objects.create(survey=survey, is_anonymous=True)
                else:
                    if request.user.is_authenticated:
                        response, created = survey.responses.get_or_create(user=request.user)
                    else:
                        response = Response.objects.create(survey=survey, is_anonymous=True)

                for question in survey.questions.all():
                    if question.question_type == SurveyQuestion.TEXT:
                        text_answer = form.cleaned_data.get(f'text_answer_{question.id}')
                        Answer.objects.create(response=response, question=question, text_answer=text_answer)
                    elif question.question_type in [SurveyQuestion.RADIO, SurveyQuestion.SELECT]:
                        choice_id = form.cleaned_data.get(f'choice_answer_{question.id}')
                        if choice_id:
                            choice_answer = question.choices.get(id=choice_id)
                            Answer.objects.create(response=response, question=question, choice_answer=choice_answer)
                    elif question.question_type == SurveyQuestion.INTEGER:
                        integer_answer = form.cleaned_data.get(f'integer_answer_{question.id}')
                        if integer_answer is not None:
                            Answer.objects.create(response=response, question=question, integer_answer=integer_answer)
                return redirect('user_survey_list')  
        else:
            form = AnswerForm(survey=survey)

        return render(request, 'user_survey_answer.html', {'survey': survey, 'form': form})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while answering the survey.'})


@login_required
def user_delete_survey(request, survey_id):
    """
    Handles deletion of a survey by the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to be deleted.

    Returns:
        HttpResponse: Redirects to 'user_survey_list' if the survey is successfully deleted.
                      Renders a confirmation page ('confirm_delete.html') with the survey details if the request method is GET.
                      Returns a forbidden HTTP response if the logged-in user did not create the survey.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)
        
        if survey.created_by != request.user:
            return HttpResponseForbidden("You are not allowed to delete this survey.")
        
        if request.method == 'POST':
            survey.delete()
            return redirect('user_survey_list')
        
        return render(request, 'confirm_delete.html', {'survey': survey})
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while deleting the survey.'})


@login_required
def user_edit_survey(request, survey_id):
    """
    Allows a logged-in user to edit an existing survey, including its questions and choices.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to be edited.

    Returns:
        HttpResponse: Redirects to 'user_survey_list' upon successful survey update.
                      Renders 'user_survey_edit.html' template with survey, survey_form, question_forms, and choice_forms in the context for GET requests.
    """
    try: 
        survey = get_object_or_404(Survey, id=survey_id)
        
        if request.method == 'POST':
            survey_form = SurveyForm(request.POST, instance=survey)
            question_forms = []
            choice_forms = []
            
            if survey_form.is_valid():
                survey = survey_form.save(commit=False)
                survey.save()
                
                for question in survey.questions.all():
                    question_form = SurveyQuestionForm(request.POST, instance=question, prefix=f'question_{question.id}')
                    question_forms.append(question_form)
                    
                    if question_form.is_valid():
                        question = question_form.save(commit=False)
                        question.save()
                        
                        for choice in question.choices.all():
                            choice_form = SurveyChoiceForm(request.POST, instance=choice, prefix=f'choice_{choice.id}')
                            choice_forms.append(choice_form)
                            
                            if choice_form.is_valid():
                                choice_form.save()
                
                return redirect('user_survey_list')  
        
        else:
            survey_form = SurveyForm(instance=survey)
            question_forms = [SurveyQuestionForm(instance=question, prefix=f'question_{question.id}') for question in survey.questions.all()]
            choice_forms = [SurveyChoiceForm(instance=choice, prefix=f'choice_{choice.id}') for question in survey.questions.all() for choice in question.choices.all()]
        
        context = {
            'survey': survey,
            'survey_form': survey_form,
            'question_forms': question_forms,
            'choice_forms': choice_forms,
        }
        
        return render(request, 'user_survey_edit.html', context)
    except Exception as e:
        return render(request, 'error.html', {'error_message': 'An error occurred while editing the survey.'})


# bar chart , pie chart 
@login_required
def user_survey_analytics(request, survey_id):
    """
    Generates analytics for a specific survey, including response counts and visual representation.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey for which analytics are to be generated.

    Returns:
        HttpResponse: Renders 'user_survey_analytics.html' template with survey, question_data, and response rate in the context.
    """
    try:
        survey = get_object_or_404(Survey, pk=survey_id)
        questions = SurveyQuestion.objects.filter(survey=survey)
        
        # Calculate total responses
        total_responses = Response.objects.filter(survey=survey).count()

        # Define the total number of possible respondents
        total_possible_respondents = CustomUser.objects.filter(is_active=True).count()

        # Calculate response rate
        response_rate = round(((total_responses / total_possible_respondents) * 100 if total_possible_respondents > 0 else 0), 2)

        def get_response_counts(question):
            answers = Answer.objects.filter(question=question)
            response_counts = {}
            for answer in answers:
                if answer.integer_answer is not None:
                    choice_text = str(answer.integer_answer)
                    response_counts[choice_text] = response_counts.get(choice_text, 0) + 1
                elif answer.choice_answer:
                    choice_text = answer.choice_answer.choice_text
                    response_counts[choice_text] = response_counts.get(choice_text, 0) + 1
                elif answer.text_answer:
                    response_counts['Text Response'] = response_counts.get('Text Response', 0) + 1
            return response_counts

        question_data = []

        for question in questions:
            response_counts = get_response_counts(question)
            img_filename = f'survey_responses_distribution_{question.id}.png'
            img_path = os.path.join(settings.MEDIA_ROOT, img_filename)

            # Prepare the data for rendering in the template
            question_entry = {
                'question_text': question.question_text,
                'responses': response_counts,
                'img_path': os.path.join(settings.MEDIA_URL, img_filename)
            }

            # Generate the bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(list(response_counts.keys()), list(response_counts.values()), width=0.5, color='skyblue')
            ax.set_xlabel('Responses')
            ax.set_ylabel('Counts')
            ax.set_title(f'Question: {question.question_text}')
            ax.grid(True)
            
            # Annotate the bars with the counts
            for bar, count in zip(bars, response_counts.values()):
                height = bar.get_height()
                ax.annotate(f'{count}', xy=(bar.get_x() + bar.get_width() / 2, height), 
                            xytext=(0, 3),  
                            textcoords="offset points",
                            ha='center', va='bottom')

            # Save the bar chart image
            plt.tight_layout()
            plt.savefig(img_path)
            plt.close(fig)

            # Generate the pie chart (example for choice answers only)
            if any(isinstance(answer.choice_answer, SurveyChoice) for answer in Answer.objects.filter(question=question)):
                pie_img_filename = f'survey_responses_pie_{question.id}.png'
                pie_img_path = os.path.join(settings.MEDIA_ROOT, pie_img_filename)
                labels = list(response_counts.keys())
                sizes = list(response_counts.values())
                plt.figure(figsize=(8, 8))
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
                plt.title(f'Pie Chart: {question.question_text}')
                plt.axis('equal')

                # Save the pie chart image
                plt.savefig(pie_img_path)
                plt.close()

                question_entry['pie_img_path'] = os.path.join(settings.MEDIA_URL, pie_img_filename)

            # Generate the line chart (example for integer answers only)
            if any(isinstance(answer.integer_answer, int) for answer in Answer.objects.filter(question=question)):
                line_img_filename = f'survey_responses_line_{question.id}.png'
                line_img_path = os.path.join(settings.MEDIA_ROOT, line_img_filename)
                x_values = range(1, len(response_counts) + 1)
                y_values = list(response_counts.values())
                plt.figure(figsize=(10, 6))
                plt.plot(x_values, y_values, marker='o', linestyle='-', color='green')
                plt.xlabel('Response Index')
                plt.ylabel('Counts')
                plt.title(f'Line Chart: {question.question_text}')
                plt.grid(True)
                plt.tight_layout()

                # Save the line chart image
                plt.savefig(line_img_path)
                plt.close()

                question_entry['line_img_path'] = os.path.join(settings.MEDIA_URL, line_img_filename)

            # Append question data entry
            question_data.append(question_entry)

        context = {
            'survey': survey,
            'question_data': question_data,
            'response_rate': response_rate,
        }

        return render(request, 'user_survey_analytics.html', context)
    
    except Exception as e:
        return HttpResponse(f"An error occurred while generating survey analytics: {str(e)}", status=500)

@login_required
def export_survey_responses_csv(request, survey_id):
    """
    Export survey responses to a CSV file.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to export responses for.

    Returns:
        HttpResponse: A CSV file containing survey responses.
    """
    try:
        # Retrieve the survey object or return 404 if not found
        survey = get_object_or_404(Survey, id=survey_id)

        # Check if the current user has permission to export responses for this survey
        if survey.created_by != request.user:
            return HttpResponse("You do not have permission to export responses for this survey.", status=403)

        # Fetch questions and responses related to the survey
        questions = SurveyQuestion.objects.filter(survey=survey)
        survey_responses = Response.objects.filter(survey=survey)

        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{survey.title}_responses.csv"'

        writer = csv.writer(response)
        writer.writerow(['Respondent', 'Question', 'Answer'])

        # Iterate through responses and answers to write to CSV
        for survey_response in survey_responses:
            for answer in survey_response.answers.all():
                respondent = 'Anonymous' if survey_response.is_anonymous else survey_response.user.username
                question_text = answer.question.question_text

                # Determine the answer text based on answer type
                if answer.text_answer is not None:
                    answer_text = answer.text_answer
                elif answer.choice_answer is not None:
                    answer_text = answer.choice_answer.choice_text
                elif answer.integer_answer is not None:
                    answer_text = str(answer.integer_answer)  # Ensure integer is converted to string
                else:
                    answer_text = 'N/A'

                writer.writerow([respondent, question_text, answer_text])

        return response

    except Exception as e:
        # Print the error to console or log it
        return HttpResponse(f"An error occurred while exporting survey responses: {str(e)}", status=500)


# poll analytics
def user_export_votes_csv(request, question_id):
    """
    Export votes for a specific question to a CSV file.

    This view retrieves all votes associated with the specified question and
    writes the vote details to a CSV file. The CSV file includes columns for
    the username, question text, choice text, vote date, and session key.

    Parameters:
    - request: The HTTP request object.
    - question_id: The ID of the question for which votes should be exported.

    Returns:
    - HttpResponse: A response with a CSV file containing the vote details.
    """
    try:
        # Get the question
        question = Question.objects.get(pk=question_id)
        
        # Create the HttpResponse object with the appropriate CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="votes_{question_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Username', 'Question', 'Choice', 'Vote Date', 'Session Key'])

        votes = Vote.objects.filter(question=question)
        for vote in votes:
            writer.writerow([
                vote.user.username if vote.user else 'Anonymous',
                vote.question.question_text,
                vote.choice.choice_text,
                vote.vote_date,
                vote.session_key
            ])

        return response
    except Question.DoesNotExist:
        messages.error(request, f"Question with ID {question_id} does not exist.")
        return redirect('user_dashboard')  
    except Exception as e:
        messages.error(request, f"An error occurred while generating the CSV: {e}")
        return redirect('user_dashboard')  

    # managing survey link-start
def generate_private_link(request, survey_id):
    if request.method == 'POST':
        respondent_email = request.POST.get('email')  
        survey = get_object_or_404(Survey, id=survey_id)
        survey_title = survey.title
        
        # Check if the email exists in CustomUser model
        if respondent_email and CustomUser.objects.filter(email=respondent_email).exists():
            if Response.objects.filter(user__email=respondent_email, survey=survey).exists():
                messages.error(request, "This email has already responded to this survey.")
                return render(request, 'user_private_link.html', {'survey_id': survey_id,'survey_title': survey_title})
            else:
                messages.error(request, "This email is not register or invalid.")

            private_link = PrivateSurveyLink.objects.create(survey=survey, respondent_email=respondent_email)
            # Build the URL for the answer page
            link_url = request.build_absolute_uri(reverse('answer_private_survey', args=[private_link.link_uuid]))
            
            # Optionally, print the link to the console for debugging
            
            # Send an email to the respondent
            # send_mail(
            #     'Private Survey Link',
            #     f'Here is your private survey link: {link_url}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     [respondent_email],
            #     fail_silently=False,
            # )
            
            # Render a template with the link instead of sending an email
            return render(request, 'private_link_display.html', {'link_url': link_url})
        
        else:
            # If email doesn't exist or not provided, handle accordingly (e.g., show error message)
            messages.error(request, "Invalid email provided or email does not exist in our records.")
            return render(request, 'user_private_link.html', {'survey_id': survey_id})
    
    # If GET request, render the form to generate the private link
    return render(request, 'user_private_link.html', {'survey_id': survey_id})


def answer_private_survey(request, link_uuid):

    """
    Generate a private link for a respondent to answer a survey.

    This view handles both GET and POST requests. For GET requests, it renders a form to input the respondent's email.
    For POST requests, it checks if the respondent's email exists in the CustomUser model and if they have already
    responded to the survey. If valid, it generates a private link for the respondent to answer the survey.

    Parameters:
    - request: The HTTP request object.
    - survey_id: The ID of the survey for which the private link should be generated.

    Returns:
    - HttpResponse: A response rendering the form or the generated private link.
    """
    try:
        if not request.user.is_authenticated:
            return redirect('login')

        private_link = get_object_or_404(PrivateSurveyLink, link_uuid=link_uuid)

        if private_link.is_used:
            return HttpResponse('This link has already been used')

        if request.user.email != private_link.respondent_email:
            return HttpResponse('This survey link is not accessible to you.')

        survey = private_link.survey

        if Response.objects.filter(user=request.user, survey=survey).exists():
            return HttpResponse("You have already responded to this survey")

        if request.method == 'POST':
            form = AnswerForm(request.POST, survey=survey)
            if form.is_valid():
                try:
                    # Create a Response instance
                    response = Response.objects.create(user=request.user, survey=survey)

                    # Process the form data and save answers
                    for question in survey.questions.all():
                        if question.question_type == SurveyQuestion.TEXT:
                            text_answer = form.cleaned_data.get(f'text_answer_{question.id}')
                            Answer.objects.create(response=response, question=question, text_answer=text_answer)
                        elif question.question_type in [SurveyQuestion.RADIO, SurveyQuestion.SELECT]:
                            choice_answer_id = form.cleaned_data.get(f'choice_answer_{question.id}')
                            choice = get_object_or_404(SurveyChoice, id=choice_answer_id)
                            Answer.objects.create(response=response, question=question, choice_answer=choice)
                        elif question.question_type == SurveyQuestion.INTEGER:
                            integer_answer = form.cleaned_data.get(f'integer_answer_{question.id}')
                            Answer.objects.create(response=response, question=question, integer_answer=integer_answer)
                        elif question.question_type == SurveyQuestion.RATING:
                            rating_answer = form.cleaned_data.get(f'rating_answer_{question.id}')
                            Answer.objects.create(response=response, question=question, rating_answer=rating_answer)

                    # Mark the private link as used after processing the form
                    private_link.is_used = True
                    private_link.save()

                    # Redirect or render a success page
                    return redirect('private_survey_answered', survey_id=survey.id)

                except Choice.DoesNotExist as choice_not_found:
                    messages.error(request, f"Error processing form: {choice_not_found}. Please try again.")
                except Exception as e:
                    messages.error(request, f"An error occurred: {e}. Please try again.")
                    # Optionally, log the exception for debugging purposes

            else:
                messages.error(request, "Invalid form submission. Please check your answers and try again.")

        else:
            form = AnswerForm(survey=survey)

        return render(request, 'user_private_link_answer.html', {'survey': survey, 'form': form})
    except Survey.DoesNotExist:
        messages.error(request, f"Survey with ID does not exist.")
        return redirect('some_error_page')  
    except Exception as e:
        messages.error(request, f"An error occurred while generating the private link: {e}")
        return redirect('some_error_page')  

def private_survey_answered(request, survey_id):
    """
    Display a thank you page after a user has completed a private survey.

    This view fetches the survey using the provided survey ID and renders a thank you page.

    Parameters:
    - request: The HTTP request object.
    - survey_id: The ID of the survey that was completed.

    Returns:
    - HttpResponse: A response rendering the thank you page.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)
        return render(request, 'user_survey_thank_you.html', {'survey': survey})
    except Survey.DoesNotExist:
        messages.error(request, "The survey does not exist.")
        return redirect('some_error_page')  # Replace 'some_error_page' with the actual error page URL
    except Exception as e:
        messages.error(request, f"An error occurred while processing your request: {e}")
        return redirect('some_error_page')  # Replace 'some_error_page' with the actual error page URL
# users managing survey-end


@login_required
def user_profile(request):
    """
    Display and handle user profile update form.

    This view allows users to update their profile information using POST method,
    and displays the profile update form for GET requests.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Renders user_profile.html template with UserProfileForm instance.
    """
    try:
        if request.method == 'POST':
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile was successfully updated!')
                return redirect('user_dashboard')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = UserProfileForm(instance=request.user)

        return render(request, 'user_profile.html', {'form': form})
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('user_dashboard')  


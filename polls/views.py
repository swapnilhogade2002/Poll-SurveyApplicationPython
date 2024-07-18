from django.shortcuts import render,get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import Question, Choice ,Vote
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages  
from survey_admin.models import Survey
from django.utils.timezone import localtime
from survey_admin.models import Survey,  Question as SurveyQuestion  ,  Choice as SurveyChoice , Answer, Response, PublicSurveyLink
from survey_admin.forms import SurveyForm, SurveyQuestionForm, SurveyChoiceForm, AnswerForm


def index(request):
    print("demo")
    """
    View function to display the list of latest questions.

    This view fetches the latest questions ordered by their publication date
    in descending order and renders them on the 'polls/index.html' template.
    
    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page displaying the list of latest questions,
                      or an error message if an exception occurs.

    Raises:
        Question.DoesNotExist: If no questions are found in the database.
        Exception: For any other exceptions that occur during execution.
    """
    try:
        print("Hi git demo")
        latest_question_list = Question.objects.order_by('-pub_date')
        context = {'latest_question_list': latest_question_list, 'page':'polls'}
        return render(request, 'polls/index.html', context)
    except Question.DoesNotExist:
        return HttpResponse("No questions found.", status=404)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def detail(request, question_id):
    """
    View function to display the details of a specific question.

    This view fetches a question based on the provided question ID, checks if
    the poll is still active based on the end time, and renders the 'polls/detail.html'
    template with the question details. If the poll is not active, it redirects to the
    index page with an error message. It also handles exceptions that might occur during
    the process.

    Args:
        request (HttpRequest): The HTTP request object.
        question_id (int): The ID of the question to fetch.

    Returns:
        HttpResponse: Rendered HTML page displaying the question details,
                      or a redirect to the index page with an error message if an
                      exception occurs.

    Raises:
        Question.DoesNotExist: If the question with the provided ID does not exist.
        Exception: For any other exceptions that occur during execution.
    """
    try:
        question = get_object_or_404(Question, pk=question_id)
        current_time = timezone.now()
        end_time = question.end_time if question.end_time else None

        if end_time and current_time > end_time:
            messages.error(request, 'Poll is not active.')
            return redirect('index') 
        return render(request, 'polls/detail.html', {'question': question})

        return render(request, 'polls/detail.html', {'question': question})
    except Question.DoesNotExist:
        messages.error(request, 'Question not found.')
        return redirect('index')
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('index')

def results(request, question_id):
    """
    View function to display the results of a specific question.

    This view fetches a question based on the provided question ID and renders the
    'polls/results.html' template with the question details. It handles exceptions
    that might occur during the process.

    Args:
        request (HttpRequest): The HTTP request object.
        question_id (int): The ID of the question to fetch.

    Returns:
        HttpResponse: Rendered HTML page displaying the question results,
                      or a redirect to the index page with an error message if an
                      exception occurs.

    Raises:
        Question.DoesNotExist: If the question with the provided ID does not exist.
        Exception: For any other exceptions that occur during execution.
    """
    try:
        question = get_object_or_404(Question, pk=question_id)
        return render(request, 'polls/results.html', { 'question': question })
    except Question.DoesNotExist:
        messages.error(request, 'Question not found.')
        return redirect('index')
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('index')




def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        messages.error(request, "You didn't select a choice.")
        return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))
        # return HttpResponse("You didn't select a choice.")
    else:
        # Record the vote
        if request.user.is_authenticated:
            # Check if the authenticated user has already voted
            if Vote.objects.filter(user=request.user, question=question).exists():
                messages.error(request, "You have already responded to the poll.")
                return render(request, 'polls/detail.html', {'question': question})
            else:
                Vote.objects.create(user=request.user, question=question, choice=selected_choice)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
            session_key = request.session.session_key
            Vote.objects.create(session_key=session_key, question=question, choice=selected_choice)

        selected_choice.votes += 1
        selected_choice.save()

        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))

def resultsData(request, obj):
    """
    Retrieve and return vote data for a specific question in JSON format.

    This view fetches the vote data for all choices of a specific question
    and returns it as a JSON response. If the question does not exist, it handles
    the exception and returns an appropriate error message.

    Args:
        request (HttpRequest): The HTTP request object.
        obj (int): The ID of the question to retrieve vote data for.

    Returns:
        JsonResponse: JSON response containing the vote data for the question.
    """
    try:
        votedata = []
        question = get_object_or_404(Question, id=obj)
        votes = question.choice_set.all()

        for vote in votes:
            votedata.append({vote.choice_text: vote.votes})

        return JsonResponse(votedata, safe=False)
    
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {e}'}, status=500)


# home surve list -start
def home_survey_list(request):
    """
    Retrieve and display the list of all surveys.

    This view fetches all surveys from the database and renders them on the
    'surveys/home_survey_list.html' template. It handles exceptions that might
    occur during the process.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page displaying the list of surveys,
                      or an error message if an exception occurs.
    """
    try:
        surveys = Survey.objects.all()
        return render(request, 'surveys/home_survey_list.html', {'surveys': surveys})
    except Survey.DoesNotExist:
        return HttpResponse("No surveys found.", status=404)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def home_answer_survey(request, survey_id):
    """
    Handle answering a survey and submitting responses.

    This view handles both GET and POST requests for answering a survey. It checks
    if the survey is active based on its end time, processes form submission for
    survey answers, and handles exceptions that might occur during the process.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to answer.

    Returns:
        HttpResponse: Rendered HTML page for answering the survey,
                      or redirects to the survey list page after form submission.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)
        now_utc = timezone.now()
        now = timezone.localtime(now_utc)

        # Convert survey end time to local time (IST)
        survey_end_time_utc = survey.end_time
        survey_end_time = timezone.localtime(survey_end_time_utc)

        # Check if current time is after survey end time
        if now > survey_end_time:
            messages.error(request, 'Survey is not active.')
            return redirect('polls:home_survey_list')  # Redirect using the namespace 'polls'
        else:
            pass
        if request.method == 'POST':
            form = AnswerForm(request.POST, survey=survey)

            if form.is_valid():
                if form.cleaned_data['is_anonymous']:
                    response = Response.objects.create(survey=survey, is_anonymous=True)
                else:
                    if request.user.is_authenticated:
                        # Check if the user has already responded to the survey
                        existing_response = Response.objects.filter(survey=survey, user=request.user).first()
                        if existing_response:
                            messages.error(request, "You have already responded to this survey!")
                            return redirect('polls:home_survey_list')
                        response = Response.objects.create(survey=survey, user=request.user)
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

                messages.success(request, 'Survey response submitted successfully.')
                return redirect('polls:home_survey_list')  # Redirect to survey list after answering

        else:
            form = AnswerForm(survey=survey)

        return render(request, 'surveys/home_survey_answer.html', {'survey': survey, 'form': form})

    except Survey.DoesNotExist:
        messages.error(request, 'Survey not found.')
        return redirect('polls:home_survey_list')
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('polls:home_survey_list')


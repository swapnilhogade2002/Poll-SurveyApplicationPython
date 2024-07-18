import pytz
from django.shortcuts import render
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import CustomUser, Survey
from django.contrib.auth import get_user_model
import qrcode
from django.http import JsonResponse ,HttpResponseForbidden
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
from polls.models import Question, Choice, Vote
from .forms import QuestionForm, ChoiceForm
from django.forms import ValidationError, inlineformset_factory
from django.utils.decorators import decorator_from_middleware_with_args
from django.views.decorators.cache import cache_control
from django.contrib.auth import logout 
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from .models import CustomUser
from .forms import CustomUserForm
from .models import Survey,  Question as SurveyQuestion  ,  Choice as SurveyChoice , Answer, Response, PrivateSurveyLink
from .forms import SurveyForm, SurveyQuestionForm, SurveyChoiceForm, AnswerForm
import matplotlib.pyplot as plt
import os
from django.shortcuts import render
from django.conf import settings
from .models import Survey, Answer as  SurveyAnswer, Question as  SurveyQuestion
from django.utils.timezone import localtime
import csv
from .forms import UserProfileForm


def nocache(view_func):
    """
    Decorator to add cache control headers to a view function.

    This decorator wraps the given view function with cache control headers
    to prevent caching by setting 'no_cache', 'must_revalidate', and 'no_store'.
    It handles exceptions that might occur during the process.

    Args:
        view_func (function): The view function to decorate.

    Returns:
        function: Decorated view function with added cache control headers.
    """
    try:
        @cache_control(no_cache=True, must_revalidate=True, no_store=True)
        def new_view_func(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        
        return new_view_func
    
    except Exception as e:
        # Handle any exceptions that might occur during decorator creation
        raise RuntimeError(f"Error creating nocache decorator: {e}")

def admin_login_page(request):
    """
    Render the admin login page.

    This view renders the 'admin_login.html' template for displaying the admin
    login page. It handles exceptions that might occur during the rendering process.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for the admin login.
    """
    try:
        return render(request, 'admin_login.html')
    except Exception as e:
        raise RuntimeError(f"Error rendering admin login page: {e}")


def admin_logout(request):
    """
    Perform logout for the admin user.

    This view logs out the current admin user by calling Django's `logout` function
    and redirects them to the 'admin_login' page. It handles exceptions that might
    occur during the logout process.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirect to the 'admin_login' page after logout.
    """
    try:
        logout(request)
        return redirect('admin_login')
    except Exception as e:
        raise RuntimeError(f"Error during admin logout: {e}")

@login_required
def admin_dashoard(request):
    """
    Render the admin dashboard page.

    This view renders the 'admin_dashboard.html' template for displaying the admin
    dashboard. It retrieves counts of users, polls, and surveys from the database,
    checks if multi-factor authentication (MFA) is enabled for the current user,
    and handles exceptions that might occur during the process.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for the admin dashboard.
    """
    try:
        users_count = CustomUser.objects.count()
        polls_count = Question.objects.count() 
        surveys_count = Survey.objects.count() 
        mfa_enabled = request.user.mfa_enabled  
        username = request.user.username

        context = {
            'users_count': users_count,
            'polls_count':polls_count,
            'surveys_count':surveys_count,
            'mfa_enabled': mfa_enabled,
            'username':username,

        }
        return render(request, 'admin_dashboard.html' ,context)
    except Exception as e:
        raise RuntimeError(f"Error rendering admin dashboard: {e}")


def user_dashoard(request):
    """
    Render the user dashboard page.

    This view renders the 'user/user_dashboard.html' template for displaying the user
    dashboard. It handles exceptions that might occur during the rendering process.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for the user dashboard.
    """
    try:
        return render(request, 'user/user_dashboard.html')
    except Exception as e:
        raise RuntimeError(f"Error rendering user dashboard: {e}")

def admin_mfa_page(request):
    """
    Handle admin login with MFA (Multi-Factor Authentication) page.

    This view handles the admin login process with MFA. It retrieves counts of users, polls, and surveys
    from the database and checks if the login request is a POST method. If the credentials are valid and
    MFA is enabled for the user, it redirects to the appropriate OTP verification page. If MFA is not enabled,
    it renders the respective dashboard (admin or user). If the credentials are invalid, it displays an error
    message and renders the admin login page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for admin login or redirected page based on MFA status.
    """
    try:
        users_count = CustomUser.objects.count()
        polls_count = Question.objects.count()
        surveys_count = Survey.objects.count()
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = authenticate(request, username=email, password=password)

            if user is not None and user.is_active:
                if user.role == 'admin':
                    login(request, user)
                    if user.mfa_enabled:
                        return redirect('otp_verification_page')
                    else:
                        return render(request, 'admin_dashboard.html', {'username': user.username, 'mfa_enabled': user.mfa_enabled, 'users_count': users_count,
                        'polls_count': polls_count, 'surveys_count':surveys_count })
                else:
                    login(request, user)
                    if user.mfa_enabled:
                        return redirect('user_otp_verification_page')
                    else:
                        return redirect('user_dashboard')
            else:
                messages.error(request, 'Invalid credentials. Please try again.') 
                return render(request, 'admin_login.html', {'error': 'Invalid email or password'})
        return render(request, 'admin_login.html')
    except Exception as e:
        raise RuntimeError(f"Error handling admin MFA page: {e}")


def admin_otp_verification_page(request):
    """
    Handle admin OTP (One-Time Password) verification page.

    This view handles the OTP verification process for admin users with MFA (Multi-Factor Authentication).
    It generates a TOTP (Time-based One-Time Password) using the user's secret key stored in `user.mfa_secret_key`.
    If the entered OTP matches the generated OTP, it updates the user's MFA status to enabled and redirects to
    the admin dashboard. If the OTP is invalid, it displays an error message and renders the OTP verification page again.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for OTP verification or redirected page based on OTP validation.
    """
    try:
        user = request.user
        totp = pyotp.TOTP(user.mfa_secret_key)

        if request.method == 'POST':
            entered_otp = request.POST.get('otp')

            if totp.verify(entered_otp):
                user.mfa_enabled = True
                user.save()
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
                return render(request, 'otp_verification_page.html')
        return render(request, 'otp_verification_page.html')
    except Exception as e:
        raise RuntimeError(f"Error handling admin OTP verification page: {e}")


def user_otp_verification_page(request):
    """
    Handle user OTP (One-Time Password) verification page.

    This view handles the OTP verification process for regular users with MFA (Multi-Factor Authentication).
    It generates a TOTP (Time-based One-Time Password) using the user's secret key stored in `user.mfa_secret_key`.
    If the entered OTP matches the generated OTP, it updates the user's MFA status to enabled and redirects to
    the user dashboard. If the OTP is invalid, it displays an error message and renders the OTP verification page again.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page for OTP verification or redirected page based on OTP validation.
    """
    try:
        user = request.user
        totp = pyotp.TOTP(user.mfa_secret_key)

        if request.method == 'POST':
            entered_otp = request.POST.get('otp')

            if totp.verify(entered_otp):
                # Update MFA status for the user
                user.mfa_enabled = True
                user.save()
                return redirect('user_dashboard')
            else:
                # Invalid OTP entered
                messages.error(request, 'Invalid OTP. Please try again.')
                return render(request, 'user_otp_verification_page.html')
        return render(request, 'user_otp_verification_page.html')
    except Exception as e:
        raise RuntimeError(f"Error handling user OTP verification page: {e}")


# QR code generation and verfication of OTP for MFA -start
def generate_qr_code(request):
    """
    Generate a QR code for Multi-Factor Authentication (MFA).

    This view generates a QR code containing the OTP authentication URL for MFA using the user's secret key.
    It uses the `pyotp` library to generate the current OTP and `qrcode` library to create the QR code image.
    The QR code image is then encoded as base64 and passed to the template for rendering.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML page displaying the QR code image for MFA.
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
            return render(request, 'generate_qr_code.html', {'qr_code_image': qr_code_image_base64})
        else:
            return HttpResponse("MFA secret key not found.")
    except Exception as e:
        return HttpResponse(f"Error generating QR code: {e}")


# disabling mfa -admin
@login_required
def disable_mfa(request):
    """
    Disable Multi-Factor Authentication (MFA) for the current user.

    This view disables MFA for the authenticated user by setting `request.user.mfa_enabled` to False
    and saving the user instance. It then displays a success message and redirects to the admin dashboard.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirect to the admin dashboard after disabling MFA.
    """
    try:
        if request.method == 'POST':
            request.user.mfa_enabled = False
            request.user.save()
            messages.success(request, 'Multi-Factor Authentication has been disabled.')
            return redirect('admin_dashboard') 
    except Exception as e:
        messages.error(request, f"Error disabling Multi-Factor Authentication: {e}")
    return redirect('admin_dashboard')


@login_required
def verify_otp(request):
    """
    Verify OTP (One-Time Password) entered by the user for Multi-Factor Authentication (MFA).

    This view handles the verification of OTP entered by the user. If the OTP is valid,
    it updates the `mfa_enabled` status for the user and redirects them to the appropriate dashboard
    based on their role (admin or user). If the OTP is invalid, it displays an error message and
    redirects the user to re-verify using a QR code.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the appropriate dashboard or QR code generation page based on the verification result.
    """
    try:
        if request.method == 'POST':
            entered_otp = request.POST.get('otp', '')

            totp = TOTP(request.user.mfa_secret_key) 
            validate_otp = totp.verify(entered_otp)

            if validate_otp:
                request.user.mfa_enabled = True
                request.user.save()

                if request.user.role == 'admin':
                    messages.success(request, 'OTP verified successfully. Multi-Factor Authentication enabled.')
                    return redirect('admin_dashboard')  
                elif request.user.role == 'user':
                    messages.success(request, 'OTP verified successfully. Multi-Factor Authentication enabled.')
                    return redirect('user_dashboard')  
                else:
                    messages.error(request, 'Role not supported for MFA.')
                    return redirect('user_dashboard')  
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
                
                totp = pyotp.TOTP(request.user.mfa_secret_key)
                qr_code_image = totp.provisioning_uri(name=request.user.username, issuer_name='YourApp')
                
                context = {
                    'qr_code_image': qr_code_image
                }
                return redirect('generate_qr_code')

        return redirect('verify_otp') 
    except Exception as e:
        messages.error(request, f"Error verifying OTP: {e}")
    return redirect('verify_otp')
# QR code generation and verfication of OTP for MFA -end


# user registration-start
def user_registration(request):
    """
    Handle user registration process.

    This view handles user registration using POST method. It validates the form data,
    checks if the passwords match, checks if the email is already taken, creates a new user,
    sets default role and state, and optionally authenticates the user after registration.
    It displays success or error messages accordingly.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the user registration form or redirects to login page after registration.
    """
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'user/user_registration.html')

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email is already taken.")
                return render(request, 'user/user_registration.html')

            user = CustomUser.objects.create_user(username=username, email=email, password=password)

            user.role = 'user' 
            user.state = CustomUser.CustomUserState.PENDING  
            user.save()

            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user is not None:
                messages.success(request, "Registration successful. You can now log in.")
                return redirect('admin_login') 
            else:
                messages.error(request, "Failed to authenticate user.")
                return render(request, 'user/user_registration.html')

        return render(request, 'user/user_registration.html')
    except Exception as e:
        messages.error(request, f"Error during registration: {e}")
    return render(request, 'user/user_registration.html')
# user registration-end


#Admin manages users data-start
@login_required
def user_list(request):
    """
    Render a list of all users.

    Retrieves all CustomUser objects from the database and renders them in a template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'user_list.html' template with a context containing all users.
    """
    try:
        users = CustomUser.objects.all()
        return render(request, 'user_list.html', {'users': users})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error fetching user list: {e}"})


@login_required
def user_detail(request, pk):
    """
    Render details of a specific user.

    Retrieves a specific CustomUser object from the database based on the primary key (`pk`)
    and renders the details in a template.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the user to retrieve.

    Returns:
        HttpResponse: Renders the 'user_detail.html' template with details of the requested user.
                      If the user with the given primary key (`pk`) does not exist, a 404 page is rendered.
    """
    try:
        user = get_object_or_404(CustomUser, pk=pk)
        return render(request, 'user_detail.html', {'user': user})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error fetching user details: {e}"})

@login_required
def user_create(request):
    """
    Create a new user.

    Renders a form to create a new CustomUser. Handles form submission to save the new user
    to the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'user_form.html' template with a form to create a new user.
                      On successful form submission, redirects to 'user_list' view.
    """
    try:
        if request.method == 'POST':
            form = CustomUserForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('user_list')
        else:
            form = CustomUserForm()
        return render(request, 'user_form.html', {'form': form})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error creating user: {e}"})

@login_required
def user_update(request, pk):
    """
    Update an existing user.

    Renders a form to update an existing CustomUser. Handles form submission to update
    the user's information in the database.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the user to update.

    Returns:
        HttpResponse: Renders the 'user_form.html' template with a form to update the user.
                      On successful form submission, redirects to 'user_list' view.
    """
    try: 
        user = get_object_or_404(CustomUser, pk=pk)
        if request.method == 'POST':
            form = CustomUserForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                return redirect('user_list')
            else:
                pass
        else:
            form = CustomUserForm(instance=user)
        return render(request, 'user_form.html', {'form': form})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error updating user: {e}"})



@login_required
def user_delete(request, pk):
    """
    Delete a user.

    Renders a confirmation page to delete an existing CustomUser. Handles POST request
    to delete the user from the database.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the user to delete.

    Returns:
        HttpResponse: Renders the 'user_confirm_delete.html' template with user details.
                      On successful deletion, redirects to 'user_list' view.
    """
    try:
        user = get_object_or_404(CustomUser, pk=pk)
        if request.method == 'POST':
            user.delete()
            return redirect('user_list')
        return render(request, 'user_confirm_delete.html', {'user': user})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error deleting user: {e}"})
#Admin manages users data-end


# admin  manage polls-start
@login_required
def poll_list(request):
    """
    Display a list of polls.

    Retrieves all Question objects from the database, prefetching related Choice objects
    to optimize performance. Renders the 'polls/poll_list.html' template with the retrieved polls.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'polls/poll_list.html' template with 'polls' context variable
                      containing the retrieved Question objects.
    """
    try: 
        polls = Question.objects.all().prefetch_related('choice_set')
        return render(request, 'polls/poll_list.html', {'polls': polls})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error fetching polls: {e}"})

@login_required
def poll_create(request):
    """
    Create a new poll.

    Handles POST requests to create a new Question object with associated Choices.
    Validates input fields for question text, start time, end time, and choices.
    Redirects to 'poll_list' view upon successful creation of the poll.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'polls/poll_create.html' template with validation errors
                      or redirects to 'poll_list' view upon successful poll creation.
    """
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        start_time = request.POST.get('start_time') 
        end_time = request.POST.get('end_time')  
        if not question_text:
            return render(request, 'polls/poll_create.html', {'error_message': 'Question text is required.'})
        try:
            question = Question.objects.create(question_text=question_text, created_by=request.user, 
            pub_date=timezone.now(), start_time=start_time,
            end_time=end_time)
        except ValidationError as e:
            return render(request, 'polls/poll_create.html', {'error_message': f"Validation Error: {e}"})
        except Exception as e:
            return render(request, 'polls/poll_create.html', {'error_message': f"Error creating poll: {e}"})

        choice_texts = request.POST.getlist('choice_text')
        if not choice_texts or len(choice_texts) < 2:
            question.delete()
            return render(request, 'polls/poll_create.html', {'error_message': 'At least two choices are required.'})

        for choice_text in choice_texts:
            Choice.objects.create(question=question, choice_text=choice_text)

        return redirect('poll_list')  
    return render(request, 'polls/poll_create.html')


@login_required
def poll_detail(request, poll_id):
    """
    Display details of a poll.

    Retrieves a Question object with the given poll_id or returns a 404 error if not found.
    Renders the 'polls/poll_detail.html' template with the poll object.

    Args:
        request (HttpRequest): The HTTP request object.
        poll_id (int): The ID of the poll to display.

    Returns:
        HttpResponse: Renders the 'polls/poll_detail.html' template with the poll details.
    """
    try:
        poll = get_object_or_404(Question, pk=poll_id)
        return render(request, 'polls/poll_detail.html', {'poll': poll})
    except Exception as e:
        return render(request, 'polls/poll_detail.html', {'error_message': f"Error fetching poll details: {e}"})



@login_required
def poll_update(request, poll_id):
    """
    Update a poll and its choices.

    Retrieves a Question object with the given poll_id or returns a 404 error if not found.
    Initializes a formset for updating related Choice objects.
    Handles POST requests to update the Question and its associated Choices if valid.
    Renders the 'polls/poll_update.html' template with the form and formset for updating.

    Args:
        request (HttpRequest): The HTTP request object.
        poll_id (int): The ID of the poll to update.

    Returns:
        HttpResponse: Redirects to 'poll_detail' view on successful update.
                      Renders 'polls/poll_update.html' with form and formset for updating.
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
                
                return redirect('poll_detail', poll_id=poll.id)
        else:
            form = QuestionForm(instance=poll)
            formset = ChoiceFormSet(instance=poll)
        
        return render(request, 'polls/poll_update.html', {'form': form, 'formset': formset})
    except Exception as e:
        return render(request, 'polls/poll_update.html', {'error_message': f"Error updating poll: {e}"})


@login_required
def poll_delete(request, poll_id):
    """
    Delete a poll.

    Retrieves a Question object with the given poll_id or returns a 404 error if not found.
    Handles POST requests to delete the Question object.
    Redirects to 'poll_list' view after successful deletion.

    Args:
        request (HttpRequest): The HTTP request object.
        poll_id (int): The ID of the poll to delete.

    Returns:
        HttpResponse: Redirects to 'poll_list' view after deletion.
                      Renders 'polls/poll_confirm_delete.html' for confirmation.
    """
    try:
        poll = get_object_or_404(Question, pk=poll_id)
        if request.method == "POST":
            poll.delete()
            return redirect('poll_list')
        return render(request, 'polls/poll_confirm_delete.html', {'poll': poll})
    except Exception as e:
        return render(request, 'polls/poll_confirm_delete.html', {'error_message': f"Error deleting poll: {e}"})


# polls result in chart
@login_required
def results(request, question_id):
    """
    Display results of a poll.

    Retrieves a Question object with the given question_id or returns a 404 error if not found.
    Renders 'polls/results.html' template with the retrieved Question object.

    Args:
        request (HttpRequest): The HTTP request object.
        question_id (int): The ID of the question for which results are to be displayed.

    Returns:
        HttpResponse: Renders 'polls/results.html' with context {'question': question}.
    """
    try:
        question = get_object_or_404(Question, pk=question_id)
        return render(request, 'polls/results.html', { 'question': question })
    except Exception as e:
        return render(request, 'polls/results.html', {'error_message': f"Error displaying results: {e}"})

# views.py

@login_required
def resultsData(request, question_id):
    """
    Retrieve and display poll results data in JSON format.

    Retrieves a Question object with the given question_id or returns a 404 error if not found.
    Constructs a JSON response containing choice_text and votes for each choice in the question's choices.
    Renders 'admin_poll_results.html' template with the retrieved Question object and votedata.

    Args:
        request (HttpRequest): The HTTP request object.
        question_id (int): The ID of the question for which results data is to be retrieved.

    Returns:
        HttpResponse: Renders 'admin_poll_results.html' with context {'question': question, 'votedata': votedata}.
        JsonResponse: Returns a JSON response with {'error': 'Question not found'} if the question with question_id does not exist.
    """
    try:
        question = Question.objects.get(pk=question_id)
        votes = question.choice_set.all()

        votedata = [{'choice_text': choice.choice_text, 'votes': choice.votes} for choice in votes]

        context = {
            'question': question,
            'votedata': votedata,
        }

        return render(request, 'admin_poll_results.html', context)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)


@login_required
def dashboard(request):
    """
    Render the dashboard HTML page.
    """
    return render(request, 'admin_poll_results.html')


@login_required
def dashboard_analytics(request, question_id):
    """
    Fetch analytics for a specific survey question, including total votes and 
    percentage distribution of choices.

    Parameters:
    - request: The HTTP request object.
    - question_id: The ID of the question to fetch analytics for.

    Returns:
    - JsonResponse: A JSON response containing question text, total votes, 
      choice texts, choice votes, and choice percentages.
    """
    try:
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
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# polls management for admin-end


# survey management-start
@login_required
def admin_survey_list(request):
    """
    Display a list of all surveys for admin users.

    Retrieves all Survey objects from the database and renders them in the 'surveys/admin_survey_list.html' template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders 'surveys/admin_survey_list.html' with context {'surveys': surveys}.
    """
    try:
        surveys = Survey.objects.all()
        return render(request, 'surveys/admin_survey_list.html', {'surveys': surveys})
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})



@login_required
def admin_survey_create(request):
    """
    Render a form to create a new survey or process a submitted survey creation form.

    GET request: Renders a blank SurveyForm to create a new survey.
    POST request: Validates the submitted SurveyForm, saves the new survey with the current user as the creator,
    and redirects to the admin survey list upon successful creation.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders 'surveys/admin_survey_create.html' with a blank or validated SurveyForm,
        or redirects to 'admin_survey_list' upon successful form submission.
    """
    try:
        if request.method == 'POST':
            form = SurveyForm(request.POST)
            if form.is_valid():
                survey = form.save(commit=False)
                survey.created_by = request.user
                survey.save()
                return redirect('admin_survey_list')
        else:
            form = SurveyForm()
        return render(request, 'surveys/admin_survey_create.html', {'form': form})
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})


@login_required
def admin_question_create(request, survey_id):
    """
    Render a form to create a new question for a specific survey or process a submitted question creation form.

    GET request: Renders a blank form to create a new question for the specified survey.
    POST request: Validates the submitted form, creates a new question and associated choices (if applicable),
    and redirects to the admin survey list upon successful creation.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to which the question belongs.

    Returns:
        HttpResponse: Renders 'surveys/admin_question_create.html' with a blank or validated form and the survey,
        or redirects to 'admin_survey_list' upon successful form submission.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)

        if request.method == 'POST':
            question_text = request.POST.get('question_text')
            question_type = request.POST.get('question_type')
            
            if not question_text:
                return render(request, 'surveys/admin_question_create.html', {'survey': survey, 'error_message': 'Question text is required.'})
            
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
            
            return redirect('admin_survey_list')  # Redirect to survey list page after adding question
        
        return render(request, 'surveys/admin_question_create.html', {'survey': survey})
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})



def admin_answer_survey(request, survey_id):
    """
    Process survey answers submitted by administrators.

    Retrieves the survey based on survey_id, checks if the survey is active, and processes
    submitted survey answers using a POST request. Validates form data and creates responses
    and associated answers based on the survey questions and answer types.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to answer.

    Returns:
        HttpResponse: Renders 'surveys/admin_survey_answer.html' with a form to answer the survey
        or redirects to 'admin_survey_list' if the survey is not active or after successfully
        processing the survey answers.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)

        # Convert current UTC time to local time (IST in this case)
        now_utc = timezone.now()
        now = timezone.localtime(now_utc)

        # Convert survey end time to local time (IST)
        survey_end_time_utc = survey.end_time
        survey_end_time = timezone.localtime(survey_end_time_utc)


        # Check if current time is after survey end time
        if now > survey_end_time:
            messages.error(request, 'Survey is not active.')
            return redirect('admin_survey_list')  # Redirect using the namespace 'polls'
        else:
            pass
        
        
         # Check if the user has already responded to the survey
        if request.user.is_authenticated:
            existing_response = Response.objects.filter(survey=survey, user=request.user).first()
        else:
            existing_response = None

        if existing_response:
            messages.error(request, "You have already responded to this survey!")
            return redirect('admin_survey_list')

        if request.method == 'POST':
            form = AnswerForm(request.POST, survey=survey)

            if form.is_valid():
            
                if form.cleaned_data['is_anonymous']:
                    response = Response.objects.create(survey=survey, is_anonymous=True)
                else:
                    if request.user.is_authenticated:
                        # If not anonymous, associate response with the logged-in user
                        response, created = survey.responses.get_or_create(user=request.user)
                    else:
                        # Handle case where the user is not logged in
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

                return redirect('admin_survey_list')  

        else:
            form = AnswerForm(survey=survey)

        return render(request, 'surveys/admin_survey_answer.html', {'survey': survey, 'form': form})
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})



@login_required
def admin_edit_survey(request, survey_id):
    """
    Edit survey details, questions, and choices.

    Retrieves the survey based on survey_id and processes form submissions
    to update survey, questions, and choices. Validates forms and saves data
    if valid, redirecting to 'admin_survey_list' upon successful update.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to edit.

    Returns:
        HttpResponse: Renders 'surveys/admin_survey_edit.html' with the survey,
        survey_form, question_forms, and choice_forms for editing or redirects
        to 'admin_survey_list' after successfully updating the survey.
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
                
                # Process questions and choices
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
                
                return redirect('admin_survey_list')  
        
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
        
        return render(request, 'surveys/admin_survey_edit.html', context)
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})


@login_required
def admin_delete_survey(request, survey_id):
    """
    Delete a survey if authorized.

    Retrieves the survey based on survey_id and checks if the current user
    is authorized to delete it. If the user is not authorized, returns a
    HttpResponseForbidden. If the request method is POST, deletes the survey
    and redirects to 'admin_survey_list'. Otherwise, renders 'confirm_delete.html'
    template with the survey for confirmation.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to delete.

    Returns:
        HttpResponse: Redirects to 'admin_survey_list' upon successful deletion
        or renders 'confirm_delete.html' template with the survey for confirmation.
        Returns HttpResponseForbidden if the user is not authorized to delete the survey.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)
        
        # Ensure the survey is being deleted by its creator
        if not request.user.is_staff and survey.created_by != request.user:
            return HttpResponseForbidden("You are not allowed to delete this survey.")
        
        if request.method == 'POST':
            survey.delete()
            return redirect('admin_survey_list')
        
        return render(request, 'confirm_delete.html', {'survey': survey})
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})

@login_required
def admin_delete_question(request, question_id):
    """
    Delete a survey question.

    Retrieves the survey question based on question_id and deletes it if the
    request method is POST. Redirects to 'admin_edit_survey' view for the survey
    that the question belonged to after deletion.

    Args:
        request (HttpRequest): The HTTP request object.
        question_id (int): The ID of the question to delete.

    Returns:
        HttpResponseRedirect: Redirects to 'admin_edit_survey' view for the survey
        that the question belonged to after successful deletion.

    Raises:
        Http404: If the survey question with the provided ID does not exist.
    """
    try:
        question = get_object_or_404(SurveyQuestion, id=question_id)
        survey_id = question.survey.id
        
        if request.method == 'POST':
            question.delete()
        
        return redirect('admin_edit_survey', survey_id=survey_id)
    except Exception as e:
        return render(request, 'error.html', {'error_message': str(e)})

@login_required
def survey_analytics(request, survey_id):
    """
    Generates analytics for a specific survey, including response counts and visual representation.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey for which analytics are to be generated.

    Returns:
        HttpResponse: Renders 'admin_survey_analytics.html' template with survey, question_data, and response rate in the context.
    """
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
        question_data.append({
            'question_text': question.question_text,
            'responses': response_counts,
            'img_path': os.path.join(settings.MEDIA_URL, img_filename)
        })

        # Generate the bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(list(response_counts.keys()), list(response_counts.values()), width=0.5)
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

        plt.tight_layout()
        plt.savefig(img_path)
        plt.close(fig)

        # Retrieve answers specific to the current question
        answers = Answer.objects.filter(question=question)

        # Generate the pie chart (example for choice answers only)
        if any(isinstance(answer.choice_answer, SurveyChoice) for answer in answers):
            pie_img_filename = f'survey_responses_pie_{question.id}.png'
            pie_img_path = os.path.join(settings.MEDIA_ROOT, pie_img_filename)
            labels = list(response_counts.keys())
            sizes = list(response_counts.values())
            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title(f'Pie Chart: {question.question_text}')
            plt.axis('equal')
            plt.savefig(pie_img_path)
            plt.close()

            question_data[-1]['pie_img_path'] = os.path.join(settings.MEDIA_URL, pie_img_filename)

        # Generate the line chart (example)
        # This is a placeholder and should be adapted based on your specific requirements
        if any(isinstance(answer.integer_answer, int) for answer in answers):
            line_img_filename = f'survey_responses_line_{question.id}.png'
            line_img_path = os.path.join(settings.MEDIA_ROOT, line_img_filename)
            x_values = range(1, len(response_counts) + 1)
            y_values = list(response_counts.values())
            plt.figure(figsize=(10, 6))
            plt.plot(x_values, y_values, marker='o', linestyle='-', color='b')
            plt.xlabel('Response Index')
            plt.ylabel('Counts')
            plt.title(f'Line Chart: {question.question_text}')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(line_img_path)
            plt.close()

            question_data[-1]['line_img_path'] = os.path.join(settings.MEDIA_URL, line_img_filename)

    context = {
        'survey': survey,
        'question_data': question_data,
        'response_rate': response_rate,
    }

    return render(request, 'surveys/admin_survey_analytics.html', context)



@login_required
def export_survey_responses_csv_admin(request, survey_id):
    """
    Export survey responses to a CSV file.

    Args:
        request (HttpRequest): The HTTP request object.
        survey_id (int): The ID of the survey to export responses for.

    Returns:
        HttpResponse: A CSV file containing survey responses.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)

        questions = SurveyQuestion.objects.filter(survey=survey)
        survey_responses = Response.objects.filter(survey=survey)

        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv; charset=utf-8')
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
                    answer_text = str(answer.integer_answer) 
                else:
                    answer_text = 'N/A'

                writer.writerow([respondent, question_text, answer_text])

        return response

    except Exception as e:
        return HttpResponse(f"An error occurred while exporting survey responses: {str(e)}", status=500)

@login_required
def export_votes_csv(request, question_id):
    """
    Export votes for a specific question to a CSV file.

    Parameters:
    - request: The HTTP request object.
    - question_id: The ID of the question to export votes for.

    Returns:
    - HttpResponse: A response containing the CSV file for download.

    The CSV file contains the following columns:
    - Username: The username of the voter or 'Anonymous' if the user is not logged in.
    - Question: The text of the question.
    - Choice: The text of the chosen option.
    - Vote Date: The date and time when the vote was cast.
    - Session Key: The session key of the voter.
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
        return HttpResponse('Question not found', status=404)
    except Exception as e:
        return HttpResponse(f'An error occurred: {str(e)}', status=500)

@login_required
def admin_generate_private_link(request, survey_id):
    """
    Generate a private survey link for a specific survey and send it to a respondent's email.

    Parameters:
    - request: The HTTP request object.
    - survey_id: The ID of the survey for which the private link is being generated.

    Returns:
    - HttpResponse: Renders a template with the private survey link or an error message.

    This view:
    - Validates the respondent's email.
    - Checks if the email is registered in the CustomUser model.
    - Checks if the email has already responded to the survey.
    - Creates a PrivateSurveyLink object.
    - Builds the URL for the private survey link.
    - Optionally sends an email to the respondent with the private survey link.
    """
    try:
        if request.method == 'POST':
            respondent_email = request.POST.get('email')  
            survey = get_object_or_404(Survey, id=survey_id)
            survey_title = survey.title
            
            # Check if the email exists in CustomUser model
            if respondent_email and CustomUser.objects.filter(email=respondent_email).exists():
                if Response.objects.filter(user__email=respondent_email, survey=survey).exists():
                    messages.error(request, "This email has already responded to this survey.")
                    return render(request, 'surveys/admin_private_link.html', {'survey_id': survey_id,'survey_title': survey_title})
                else:
                    messages.error(request, "This email is not register or invalid.")

                private_link = PrivateSurveyLink.objects.create(survey=survey, respondent_email=respondent_email)
                # Build the URL for the answer page
                link_url = request.build_absolute_uri(reverse('admin_answer_private_survey', args=[private_link.link_uuid]))
                
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
                return render(request, 'surveys/private_link_display.html', {'link_url': link_url})
            
            else:
                # If email doesn't exist or not provided, handle accordingly (e.g., show error message)
                messages.error(request, "Invalid email provided or email does not exist in our records.")
                return render(request, 'surveys/admin_private_link.html', {'survey_id': survey_id})
        
        # If GET request, render the form to generate the private link
        return render(request, 'surveys/admin_private_link.html', {'survey_id': survey_id})
    except Survey.DoesNotExist:
        messages.error(request, "Survey not found.")
        return render(request, 'surveys/admin_private_link.html', {'survey_id': survey_id})
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, 'surveys/admin_private_link.html', {'survey_id': survey_id})


def admin_answer_private_survey(request, link_uuid):
    """
    Handle the private survey link answer submission.

    Parameters:
    - request: The HTTP request object.
    - link_uuid: The UUID of the private survey link.

    Returns:
    - HttpResponse: Renders the survey answer form or a success/error message.

    This view:
    - Validates the private survey link.
    - Checks if the link has already been used or if the current user is allowed to access the survey.
    - Processes the form submission to record survey answers.
    - Marks the private link as used after successful submission.
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
            else:
                messages.error(request, "Invalid form submission. Please check your answers and try again.")
        else:
            form = AnswerForm(survey=survey)

        return render(request, 'surveys/user_private_link_answer.html', {'survey': survey, 'form': form})
    except PrivateSurveyLink.DoesNotExist:
        return HttpResponse('Invalid survey link.')
    except Survey.DoesNotExist:
        return HttpResponse('Survey not found.')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return render(request, 'surveys/user_private_link_answer.html', {'form': None})

def admin_private_survey_answered(request, survey_id):
    """
    Render a thank you page after a private survey is answered.

    Parameters:
    - request: The HTTP request object.
    - survey_id: The ID of the survey that was answered.

    Returns:
    - HttpResponse: Renders the thank you page template with the survey context.

    This view:
    - Retrieves the survey object based on the provided survey_id.
    - Renders a thank you page to acknowledge the user's survey response.
    """
    try:
        survey = get_object_or_404(Survey, id=survey_id)
        return render(request, 'surveys/user_survey_thank_you.html', {'survey': survey})
    except Survey.DoesNotExist:
        messages.error(request, "Survey not found.")
        return render(request, 'surveys/user_survey_thank_you.html', {'survey': None})
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return render(request, 'surveys/user_survey_thank_you.html', {'survey': None})

# survey management-end

@login_required
def admin_profile(request):
    """
    View to handle displaying and updating the admin's profile.

    If the request method is POST, it attempts to update the profile with the provided data.
    If the request method is GET, it displays the current profile information.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Renders the profile page template with the profile form context.
    - HttpResponseRedirect: Redirects to the admin dashboard after successful profile update.
    """
    try: 
        if request.method == 'POST':
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile was successfully updated!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = UserProfileForm(instance=request.user)
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        form = UserProfileForm(instance=request.user)

    return render(request, 'admin_profile.html', {'form': form})
    


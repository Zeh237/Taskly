from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import ForgotPasswordRequestForm, OtpVerificationForm, SetNewPasswordForm, UserRegistrationForm, UserLoginForm
from .models import User
import logging

def register_view(request):
    """
    View for user registration.
    Handles displaying the registration form and processing submissions.
    Sends a verification email upon successful registration.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Generate and save OTP
            otp = random.randint(100000, 999999)
            user.otp = otp
            user.otp_created_at = timezone.now()
            logging.debug("user created")
            user.save()

            # Send Verification Email
            subject = 'Verify Your Email Address'
            message = f"""
            Hi {user.first_name},

            Thank you for registering. Please use the following One-Time Password (OTP)
            or click the link below to verify your email address:

            Your OTP: {otp}

            Verification Link: {request.build_absolute_uri(reverse('accounts:verify_email') + f'?email={user.email}&otp={otp}')}
            
            Ensure to verify the account within 1 hour, if not the OTP will expire

            If you did not register for an account, please ignore this email.

            The Team
            """
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                logging.debug("Email sent")
                # Create and pass the verification form with the user's email pre-filled
                verify_form = OtpVerificationForm(initial={'email': user.email})
                return redirect(reverse('accounts:verify_email') + f'?email={user.email}')
            except Exception as e:
                print(f"Error sending email: {e}")
                user.delete()
                return render(request, 'users/register.html', {
                    'form': form, 
                    'error': 'Failed to send verification email. Please try again.'
                })
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def verify_email_view(request):
    """
    View for verifying user's email using an OTP form.
    Checks if OTP is expired (older than 1 hour).
    """
    error_message = None
    form = None
    email_from_get = request.GET.get('email')
    otp_from_get = request.GET.get('otp')

    if request.method == 'POST':
        print('here')
        form = OtpVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = form.cleaned_data['otp']
            try:
                user = User.objects.get(email=email)

                # Check if user is already active
                if user.is_active:
                    return render(request, 'users/verification_failed.html', 
                               {'error': 'Your account is already active. Please log in.'})

                # Check if OTP is expired
                if user.is_otp_expired():
                    user.otp = None
                    user.otp_created_at = None
                    user.save()
                    error_message = 'Verification code has expired. Please request a new one.'
                    form.add_error(None, error_message)
                # Check if OTP matches and is not None
                elif user.otp is not None and str(user.otp) == otp:
                    user.is_active = True
                    user.otp = None
                    user.otp_created_at = None
                    user.save()
                    return render(request, 'users/verification_success.html')
                else:
                    error_message = 'Invalid email or verification code.'
                    form.add_error(None, error_message)

            except User.DoesNotExist:
                error_message = 'Invalid email or verification code.'
                form.add_error(None, error_message)

            except Exception as e:
                print(f"Verification error: {e}")
                error_message = 'An unexpected error occurred during verification.'
                form.add_error(None, error_message)

    elif email_from_get and otp_from_get:
        # Handle GET request with email and otp (from the email link)
        try:
            user = User.objects.get(email=email_from_get)

            # Check if user is already active
            if user.is_active:
                return render(request, 'users/verification_failed.html', 
                           {'error': 'Your account is already active. Please log in.'})

            # Check if OTP is expired
            if user.is_otp_expired():
                user.otp = None
                user.otp_created_at = None
                user.save()
                error_message = 'Verification code has expired. Please request a new one.'
                form = OtpVerificationForm(initial={'email': email_from_get})
            # Check if OTP matches and is not None
            elif user.otp is not None and str(user.otp) == otp_from_get:
                user.is_active = True
                user.otp = None
                user.otp_created_at = None
                user.save()
                return render(request, 'users/verification_success.html')
            else:
                # Invalid OTP from GET parameters
                error_message = 'Invalid verification code.'
                form = OtpVerificationForm(initial={'email': email_from_get})

        except User.DoesNotExist:
            error_message = 'User not found.'
            form = OtpVerificationForm()

        except Exception as e:
            print(f"Verification error: {e}")
            error_message = 'An unexpected error occurred during verification.'
            form = OtpVerificationForm()

    else:
        form = OtpVerificationForm()

    return render(request, 'users/verify_email.html', {'form': form, 'error': error_message})


def login_view(request):
    """
    View for user login.
    Handles displaying the login form and authenticating users.
    """
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            # Get the authenticated user object from the form's clean method
            user = form.get_user()
            if user is not None:
                # Check if the user is active
                if user.is_active:
                    login(request, user)
                    return redirect('accounts:home')
                else:
                    # User is not active, inform them to verify email
                    form.add_error(None, "Your account is not active. Please check your email to verify.")
            else:
                 form.add_error(None, "Invalid email or password.")
        pass 
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """
    View for logging out a user.
    Redirects to the login page or home page after logout.
    """
    logout(request)
    return redirect('login')


def forgot_password_request_view(request):
    """
    View for handling forgot password requests.
    Sends an email with a password reset OTP.
    """
    if request.method == 'POST':
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate and save OTP
                otp = random.randint(100000, 999999)
                user.otp = otp
                user.save()

                # Send password reset email
                subject = 'Password Reset Request'
                message = f"""
                Hi {user.first_name},

                We received a request to reset your password. Please use the following 
                One-Time Password (OTP) to verify your identity:

                Your OTP: {otp}

                Verification Link: {request.build_absolute_uri(reverse('forgot_password_verify') + f'?email={user.email}&otp={otp}')}

                If you did not request a password reset, please ignore this email.

                The Team
                """
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [user.email]

                try:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                    return render(request, 'users/forgot_password_email_sent.html', {'email': user.email})
                except Exception as e:
                    print(f"Error sending email: {e}")
                    return render(request, 'users/forgot_password.html', 
                                 {'form': form, 'error': 'Failed to send email. Please try again.'})
            except User.DoesNotExist:
                return render(request, 'users/forgot_password_email_sent.html', {'email': email})
    else:
        form = ForgotPasswordRequestForm()

    return render(request, 'users/forgot_password.html', {'form': form})


def forgot_password_verify_view(request):
    """
    View for verifying OTP during password reset process.
    """
    error_message = None
    form = None
    email_from_get = request.GET.get('email')
    otp_from_get = request.GET.get('otp')

    if request.method == 'POST':
        form = OtpVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = form.cleaned_data['otp']
            try:
                user = User.objects.get(email=email)

                # Check if OTP matches and is not None
                if user.otp is not None and str(user.otp) == otp:
                    # Store email in session for the next step
                    request.session['reset_email'] = email
                    user.otp = None 
                    user.save()
                    return redirect('forgot_password_reset')
                else:
                    error_message = 'Invalid email or verification code.'
                    form.add_error(None, error_message)

            except User.DoesNotExist:
                error_message = 'Invalid email or verification code.'
                form.add_error(None, error_message)

            except Exception as e:
                print(f"Verification error: {e}")
                error_message = 'An unexpected error occurred during verification.'
                form.add_error(None, error_message)

    elif email_from_get and otp_from_get:
        # Handle GET request with email and otp (from the email link)
        try:
            user = User.objects.get(email=email_from_get)

            # Check if OTP matches and is not None
            if user.otp is not None and str(user.otp) == otp_from_get:
                # Store email in session for the next step
                request.session['reset_email'] = email_from_get
                user.otp = None  # Clear OTP after successful verification
                user.save()
                return redirect('forgot_password_reset')
            else:
                # Invalid OTP from GET parameters
                error_message = 'Invalid verification code.'
                form = OtpVerificationForm(initial={'email': email_from_get})

        except User.DoesNotExist:
            error_message = 'User not found.'
            form = OtpVerificationForm()

        except Exception as e:
            print(f"Verification error: {e}")
            error_message = 'An unexpected error occurred during verification.'
            form = OtpVerificationForm()

    else:
        form = OtpVerificationForm()

    return render(request, 'users/forgot_password_verify.html', 
                 {'form': form, 'error': error_message})
    

def forgot_password_reset_view(request):
    """
    View for setting a new password after OTP verification.
    """
    # Check if user came from verification step
    if 'reset_email' not in request.session:
        return redirect('forgot_password_request')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            email = request.session['reset_email']
            
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Clear the session
                del request.session['reset_email']
                
                # Auto-login the user
                user = authenticate(email=email, password=new_password)
                login(request, user)
                
                return render(request, 'users/forgot_password_success.html')
            
            except User.DoesNotExist:
                form.add_error(None, 'User not found. Please try the password reset process again.')
            except Exception as e:
                print(f"Password reset error: {e}")
                form.add_error(None, 'An error occurred. Please try again.')
    else:
        form = SetNewPasswordForm()

    return render(request, 'users/forgot_password_reset.html', {'form': form})


def home_view(request):
    return HttpResponse("Hello World")
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User

class UserRegistrationForm(forms.ModelForm):
    """
    Form for user registration with Tailwind CSS classes.
    """
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            # Add Tailwind CSS classes directly to the widget attributes
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter your password' # Added placeholder for better UX
            }
        )
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(
            # Add Tailwind CSS classes directly to the widget attributes
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Confirm your password' # Added placeholder
            }
        )
    )

    # Explicitly define widgets for other fields to add Tailwind classes
    first_name = forms.CharField(
        label='First Name',
        widget=forms.TextInput(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter your first name' # Added placeholder
            }
        )
    )
    last_name = forms.CharField(
        label='Last Name',
        widget=forms.TextInput(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter your last name' # Added placeholder
            }
        )
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter your email address' # Added placeholder
            }
        )
    )


    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password_confirm'] # Ensure all fields are listed here
        # Removed the 'widgets' dictionary as we are defining them explicitly above
        # widgets = {
        #     'first_name': forms.TextInput(attrs={'class': 'form-control'}),
        #     'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        #     'email': forms.EmailInput(attrs={'class': 'form-control'}),
        # }

    def clean_password_confirm(self):
        """
        Validate that the password and password_confirm fields match.
        """
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords don't match.")
        return password_confirm

    def save(self, commit=True):
        """
        Create the user using the UserManager's create_user method.
        This handles password hashing and saving the user instance.
        """
        # Use create_user which handles password hashing
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', '')
        )
        return user
    
class UserLoginForm(forms.Form):
    """
    Form for user login with Tailwind CSS classes.
    Includes email and password fields.
    Validates credentials using Django's authenticate function.
    """
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter your email address'
            }
        )
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter your password'
            }
        )
    )

    def clean(self):
        """
        Validate the email and password against the database.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Authenticate the user
            user = authenticate(email=email, password=password)

            if user is not None:
                # Check if user is active
                if not user.is_active:
                    raise ValidationError(
                        "Your account is not active. Please verify your email first."
                    )
                self.user = user
            else:
                raise ValidationError(
                    "Invalid login credentials. Please try again."
                )

        return cleaned_data

    def get_user(self):
        """
        Helper method to retrieve the authenticated user object.
        Call this after checking if the form is valid.
        """
        return getattr(self, 'user', None)

class OtpVerificationForm(forms.Form):
    """
    Form for manually entering email and OTP for verification with Tailwind styling.
    """
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
            'placeholder': 'Enter your email address'
        })
    )
    otp = forms.CharField(
        label="One-Time Password (OTP)",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
            'placeholder': 'Enter 6-digit OTP',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )

    def clean_otp(self):
        """
        Ensure the OTP consists only of digits.
        """
        otp = self.cleaned_data.get('otp')
        if otp and not otp.isdigit():
            raise ValidationError("OTP must contain only digits.")
        return otp
    
class ForgotPasswordRequestForm(forms.Form):
    """
    Form to request a password reset email.
    """
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

class SetNewPasswordForm(forms.Form):
    """
    Form to set a new password after verification.
    """
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_new_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_confirm_new_password(self):
        """
        Validate that the new password and confirm fields match.
        """
        new_password = self.cleaned_data.get('new_password')
        confirm_new_password = self.cleaned_data.get('confirm_new_password')

        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValidationError("New passwords don't match.")
        return confirm_new_password
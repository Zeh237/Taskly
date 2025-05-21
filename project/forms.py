from django import forms
from .models import Project, ProjectMember
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectForm(forms.ModelForm):
    """
    Form for creating and updating Project instances with Tailwind CSS classes.
    """
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                    'placeholder': 'Enter project name'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                    'placeholder': 'Enter project description',
                    'rows': 4
                }
            ),
        }

class ProjectMemberForm(forms.ModelForm):
    """
    Form for adding ProjectMember instances with Tailwind CSS classes.
    """
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="User",
        widget=forms.Select(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
            }
        )
    )

    role = forms.ChoiceField(
        choices=ProjectMember.ROLE_CHOICES,
        label="Role",
        widget=forms.Select(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
            }
        )
    )

    class Meta:
        model = ProjectMember
        fields = ['user', 'role']
        
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        project = self.instance.project if self.instance and self.instance.pk else None

        if user and project:
            if ProjectMember.objects.filter(project=project, user=user).exists():
                raise forms.ValidationError(f"{user.get_full_name()} is already a member of this project.")

        return cleaned_data
    
class InviteForm(forms.Form):
    email = forms.EmailField(
        label='User Email',
        widget=forms.EmailInput(
                attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter email to invite'
            }
        )
    )

class AddMemberByEmailForm(forms.Form):
    """
    Form for adding an existing user as a project member by email.
    """
    email = forms.EmailField(
        label='User Email',
        widget=forms.EmailInput(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'placeholder': 'Enter email of existing user'
            }
        )
    )
    role = forms.ChoiceField(
        choices=[(choice[0], choice[1]) for choice in ProjectMember.ROLE_CHOICES if choice[0] != 'creator'], # Exclude 'creator' role for adding members
        label="Role",
        widget=forms.Select(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
            }
        )
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with this email address.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        project = self.project if hasattr(self, 'project') else None

        if email and project:
            try:
                user = User.objects.get(email=email)
                if ProjectMember.objects.filter(project=project, user=user).exists():
                    raise forms.ValidationError(f"{user.get_full_name()} is already a member of this project.")
            except User.DoesNotExist:
                 pass


        return cleaned_data
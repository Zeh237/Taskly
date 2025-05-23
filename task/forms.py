from django import forms
from .models import Task, ProjectMember
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class TaskForm(forms.ModelForm):
    """
    Form for creating and updating Task instances
    """
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        label="Assigned To",
        widget=forms.SelectMultiple(
            attrs={
                'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                'size': '5'
            }
        ),
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'status']
        widgets = {

            'title': forms.TextInput(
                attrs={
                    'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                    'placeholder': 'Enter task title'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                    'placeholder': 'Enter task description',
                    'rows': 4
                }
            ),
            'status': forms.Select(
                 attrs={
                    'class': 'w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition duration-200',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

        if self.project:
            self.fields['assigned_to'].queryset = User.objects.filter(project_memberships__project=self.project).distinct()
        else:
             self.fields['assigned_to'].queryset = User.objects.none()


    def clean_assigned_to(self):
        assigned_users = self.cleaned_data.get('assigned_to')

        if assigned_users and self.project:
            project_member_ids = ProjectMember.objects.filter(project=self.project).values_list('user__id', flat=True)

            for user in assigned_users:
                if user.id not in project_member_ids:
                    raise forms.ValidationError(f"{user.get_full_name()} is not a member of this project.")
        elif assigned_users and not self.project:
             raise forms.ValidationError("Cannot assign users without specifying a project.")


        return assigned_users


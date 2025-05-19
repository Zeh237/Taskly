from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('creator', 'Creator'),
        ('contributor', 'Contributor'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

class ProjectInvitation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invitations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='project_invitations')
    email = models.EmailField(null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_project_invitations')

    class Meta:
        unique_together = [('project', 'user', 'status'), ('project', 'email', 'status')]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, email__isnull=True) |
                    models.Q(user__isnull=True, email__isnull=False)
                ),
                name='user_or_email_not_null'
            )
        ]
        
    def has_expired(self):
        expiration_period = timezone.now() - timezone.timedelta(days=7)
        return self.sent_at < expiration_period
        

    def __str__(self):
        identifier = self.user.get_full_name() if self.user else self.email
        return f"Invitation for {identifier} to {self.project.name} ({self.status})"
        
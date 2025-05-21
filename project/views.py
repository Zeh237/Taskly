import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import PermissionDenied 

from .models import Project, ProjectMember, ProjectInvitation
from .forms import InviteForm, ProjectForm, ProjectMemberForm, AddMemberByEmailForm

from django.contrib.auth import get_user_model
User = get_user_model()

logger = logging.getLogger(__name__)


@login_required
def project_list(request):
    """
    View to list all projects created by or contributed to by the logged-in user.
    """
    user_projects = Project.objects.filter(created_by=request.user) | \
                    Project.objects.filter(memberships__user=request.user)
                    
    user_projects = user_projects.distinct()

    context = {
        'projects': user_projects
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_create(request):
    """
    View to create a new project.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            
            ProjectMember.objects.create(project=project, user=request.user, role='creator')

            return redirect('project:project_list')
    else:
        form = ProjectForm()

    context = {
        'form': form
    }
    return render(request, 'projects/project_create.html', context)


@login_required
def project_detail(request, pk):
    """
    View to display details of a specific project.
    """
    project = get_object_or_404(Project, pk=pk)
    if not project.memberships.filter(user=request.user).exists():
        raise PermissionDenied("You do not have permission to view this project.")

    add_member_form = AddMemberByEmailForm()
    invite_form = InviteForm()

    if request.method == 'POST':
        if 'add_member_submit' in request.POST:
            add_member_form = AddMemberByEmailForm(request.POST)
            add_member_form.project = project
            if add_member_form.is_valid():
                email = add_member_form.cleaned_data['email']
                role = add_member_form.cleaned_data['role']

                try:
                    user_to_add = User.objects.get(email=email)
                    if not ProjectMember.objects.filter(project=project, user=user_to_add).exists():
                        ProjectMember.objects.create(
                            project=project,
                            user=user_to_add,
                            role=role
                        )
                        logger.info(f"User {request.user.email} added existing user {email} to project {project.name} with role {role}")
                        return redirect('project:project_detail', pk=project.pk)
                    else:
                        add_member_form.add_error('email', f"{user_to_add.get_full_name()} is already a member of this project.")

                except User.DoesNotExist:
                    add_member_form.add_error('email', "No user found with this email address.")
                except IntegrityError:
                     add_member_form.add_error('email', f"A member with this email is already part of this project.")

        elif 'invite_member_submit' in request.POST:
             invite_form = InviteForm(request.POST)
             invite_form.project = project 
             if invite_form.is_valid():
                 invite_email = invite_form.cleaned_data['email']
                 invite_role = invite_form.cleaned_data.get('role', 'contributor')

                 if project.memberships.filter(user__email=invite_email).exists():
                     invite_form.add_error('email', f"A user with this email is already a member of {project.name}.")
                 else:
                     existing_invitation = ProjectInvitation.objects.filter(
                         project=project,
                         email=invite_email,
                         status='pending'
                     ).first()
                     if existing_invitation:
                          invite_form.add_error('email', f"An invitation has already been sent to {invite_email} for this project.")
                     else:
                         invited_user = User.objects.filter(email=invite_email).first()

                         # Create invitation
                         invitation = ProjectInvitation.objects.create(
                             project=project,
                             user=invited_user,
                             email=invite_email if not invited_user else None,
                             invited_by=request.user,
                             role=invite_role
                         )

                         # Send the invitation email
                         subject = f'Invitation to join project: {project.name}'
                         invite_link = request.build_absolute_uri(reverse('project:accept_project_invite', args=[invitation.token]))

                         message = f"""
                         Hi,

                         You've been invited by {request.user.get_full_name()} to join the project "{project.name}".

                         Project Description: {project.description}

                         To accept the invitation, click on the link below:
                         {invite_link}

                         If you did not expect this invitation, please ignore this email.

                         The Team
                         """
                         from_email = settings.DEFAULT_FROM_EMAIL
                         recipient_list = [invite_email]

                         try:
                             send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                             logger.info(f"Project invitation sent to {invite_email} for project {project.name}")
                             return redirect('project:project_detail', pk=project.pk)
                         except Exception as e:
                             logger.error(f"Error sending project invitation email to {invite_email}: {e}")
                             invite_form.add_error(None, "Failed to send invitation email. Please try again.")
        else:
            logger.warning("Unknown form submission in project_detail view.")
         
    members = project.memberships.all()

    context = {
        'project': project,
        'add_member_form': add_member_form,
        'invite_form': invite_form,
        'members': members,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_update(request, pk):
    """
    View to update an existing project.
    Only the project creator should be allowed to update.
    """
    project = get_object_or_404(Project, pk=pk)

    if project.created_by != request.user:
        raise PermissionDenied("You do not have permission to update this project.")

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'projects/project_update.html', context)


@transaction.atomic
@login_required
def project_invite(request, pk):
    """
    View to send an invitation to a user to join a project.
    Only project admins are allowed to invite.
    """
    project = get_object_or_404(Project, pk=pk)
    if not project.memberships.filter(user=request.user).exists():
         raise PermissionDenied("You do not have permission to invite members to this project.")
    if project.created_by != request.user:
        raise PermissionDenied("You do not have permission to invite members to this project.")

    if request.method == 'POST':
        form = InviteForm(request.POST)
        if form.is_valid():
            invite_email = form.cleaned_data['email']
            invite_role = form.cleaned_data.get('role', 'contributor')

            if project.memberships.filter(user__email=invite_email).exists():
                form.add_error('email', f"A user with this email is already a member of {project.name}.")
            else:
                existing_invitation = ProjectInvitation.objects.filter(
                    project=project,
                    email=invite_email,
                    status='pending'
                ).first()
                if existing_invitation:
                     form.add_error('email', f"An invitation has already been sent to {invite_email} for this project.")
                else:
                    invited_user = User.objects.filter(email=invite_email).first()

                    # Create the invitation
                    invitation = ProjectInvitation.objects.create(
                        project=project,
                        user=invited_user,
                        email=invite_email if not invited_user else None,
                        invited_by=request.user
                    )
                    
                    subject = f'Invitation to join project: {project.name}'
                    invite_link = request.build_absolute_uri(reverse('project:accept_project_invite', args=[invitation.token]))

                    message = f"""
                    Hi,

                    You've been invited by {request.user.get_full_name()} to join the project "{project.name}".

                    Project Description: {project.description}

                    To accept the invitation, click on the link below:
                    {invite_link}

                    If you did not expect this invitation, please ignore this email.

                    The Team
                    """
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [invite_email]

                    try:
                        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                        logger.info(f"Project invitation sent to {invite_email} for project {project.name}")
                        return redirect('project:project_detail', pk=project.pk)
                    except Exception as e:
                        logger.error(f"Error sending project invitation email to {invite_email}: {e}")
                        invitation.delete()
                        form.add_error(None, "Failed to send invitation email. Please try again.")

    else:
        form = InviteForm()

    context = {
        'project': project,
        'form': form,
    }
    return render(request, 'projects/project_invite.html', context)


@transaction.atomic
def accept_project_invite(request, token):
    """
    View to handle accepting a project invitation via a unique token.
    Adds the user to the project members if the invitation is valid.
    """
    invitation = get_object_or_404(ProjectInvitation, token=token, status='pending')

    # Check if the invitation has expired
    if invitation.is_expired(): 
        invitation.status = 'expired'
        invitation.save()
        return render(request, 'projects/invite_expired.html', {'invitation': invitation})

    # If the user is logged in, check if they match the invited user/email
    if request.user.is_authenticated:
        if invitation.user and invitation.user != request.user:
            logger.warning(f"Authenticated user {request.user.email} attempted to accept invitation for {invitation.user.email or invitation.email}")
            return redirect('accounts:login')
            # pass

        # If the invitation is by email and the logged-in user's email matches
        if invitation.email and invitation.email != request.user.email:
             # Logged-in user's email doesn't match the invited email
             logger.warning(f"Authenticated user {request.user.email} attempted to accept invitation for email {invitation.email}")
             return redirect('accounts:login')

        # If the user is logged in and matches the invitation criteria (user or email)
        try:
            if not ProjectMember.objects.filter(project=invitation.project, user=request.user).exists():
                 ProjectMember.objects.create(
                     project=invitation.project,
                     user=request.user,
                     role='contributor'
                 )
                 logger.info(f"User {request.user.email} accepted invitation for project {invitation.project.name}")
            else:
                 logger.info(f"User {request.user.email} is already a member of project {invitation.project.name}, invitation marked as accepted.")

            invitation.status = 'accepted'
            invitation.accepted_at = timezone.now()
            invitation.user = request.user
            invitation.save()

            return redirect('project_detail', pk=invitation.project.pk)

        except IntegrityError:
            logger.warning(f"IntegrityError when adding user {request.user.email} to project {invitation.project.name}. User is likely already a member.")
            invitation.status = 'accepted'
            invitation.accepted_at = timezone.now()
            invitation.user = request.user
            invitation.save()
            return redirect('project_detail', pk=invitation.project.pk)

    else:
        request.session['invitation_token'] = str(token)
        return redirect(settings.LOGIN_URL)


@transaction.atomic
@login_required
def project_member_remove(request, pk):
    """
    View to remove a member from a project wth permission checks
    """
    member_to_remove = get_object_or_404(ProjectMember, pk=pk)
    project = member_to_remove.project
    
    if project.created_by == request.user and member_to_remove.user != request.user:
        member_to_remove.delete()
        logger.info(f"User {request.user.email} removed member {member_to_remove.user.email} from project {project.name}")
    else:
        raise PermissionDenied("You do not have permission to remove this member.")

    return redirect('project:project_detail', pk=project.pk)

@login_required
def dashboard(request):
    return render(request, "projects/dashboard.html")
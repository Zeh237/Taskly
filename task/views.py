from django.shortcuts import redirect, render
from ..users.models import Users
from ..project.models import Project
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import TaskForm

# Create your views here.

@login_required
def create_task(request, project_id):
    project = Project.objects.get_or_404(id=project_id)
    if project.created_by != request.user:
        raise PermissionDenied("You do not have permission to create tasks in this project.")
    
    if request.method == 'POST':
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()
            return redirect('project:project_detail', pk=project_id)
        
    else:
        form = TaskForm(project=project)
    
    context = {
        "form": form,
        "project": project
    }
        
    return render(request, 'tasks/create_task.html', context)


from django.urls import path
from . import views

app_name = 'project'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/update/', views.project_update, name='project_update'),
    path('<int:pk>/invite/', views.project_invite, name='project_invite'),
    path('invite/accept/<uuid:token>/', views.accept_project_invite, name='accept_project_invite'),
    path('member/<int:pk>/remove/', views.project_member_remove, name='project_member_remove')
]

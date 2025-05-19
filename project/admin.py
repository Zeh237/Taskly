from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember, ProjectInvitation

User = get_user_model()

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'created_by__username')
    raw_id_fields = ('created_by',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'added_at')
    list_filter = ('role', 'added_at')
    search_fields = ('project__name', 'user__username')
    raw_id_fields = ('project', 'user')
    date_hierarchy = 'added_at'
    ordering = ('-added_at',)

@admin.register(ProjectInvitation)
class ProjectInvitationAdmin(admin.ModelAdmin):
    list_display = ('project', 'get_user', 'email', 'status', 'sent_at', 'invited_by')
    list_filter = ('status', 'sent_at')
    search_fields = ('project__name', 'user__username', 'email', 'token')
    raw_id_fields = ('project', 'user', 'invited_by')
    date_hierarchy = 'sent_at'
    ordering = ('-sent_at',)
    actions = ['mark_as_expired']

    fieldsets = (
        (None, {
            'fields': ('project', ('user', 'email'), 'status', 'invited_by')
        }),
        ('Token & Timestamps', {
            'fields': ('token', 'sent_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('token', 'sent_at')

    def get_user(self, obj):
        return obj.user if obj.user else obj.email
    get_user.short_description = 'User/Email'

    def mark_as_expired(self, request, queryset):
        queryset.filter(status='pending').update(status='expired')
    mark_as_expired.short_description = "Mark selected pending invitations as expired"
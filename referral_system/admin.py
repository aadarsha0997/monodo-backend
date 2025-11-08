from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, ReferralTracking


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'phone_number', 'user_type', 'referral_code', 'referred_by', 'agent', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'phone_number', 'referral_code']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('phone_number', 'withdraw_password')
        }),
        ('User Type & Referral', {
            'fields': ('user_type', 'referral_code', 'referred_by', 'agent')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone_number', 'password1', 'password2', 'withdraw_password', 'user_type', 'referred_by'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'referral_code']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # If user is an agent (not superuser), show only their users
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return qs.filter(agent=request.user).select_related('referred_by', 'agent')
        
        # Superadmins see all users
        return qs.select_related('referred_by', 'agent')
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on user type"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            # Agents see limited fields
            return (
                (None, {
                    'fields': ('username',)
                }),
                ('Personal Info', {
                    'fields': ('phone_number', 'withdraw_password')
                }),
                ('User Type & Referral', {
                    'fields': ('referral_code', 'referred_by', 'agent')
                }),
                ('Status', {
                    'fields': ('is_active',)
                }),
                ('Important Dates', {
                    'fields': ('last_login', 'date_joined')
                }),
            )
        return super().get_fieldsets(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only for agents"""
        readonly = list(self.readonly_fields)
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            # Agents cannot change these fields
            readonly.extend(['username', 'agent', 'referred_by'])
            if obj:  # When editing existing user
                readonly.append('user_type')
        
        return readonly
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form for agents"""
        form = super().get_form(request, obj, **kwargs)
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            # Limit referred_by choices to agent's users only
            if 'referred_by' in form.base_fields:
                form.base_fields['referred_by'].queryset = CustomUser.objects.filter(
                    agent=request.user
                )
        
        return form
    
    def has_add_permission(self, request):
        """Agents can add new users"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT':
            return True
        return super().has_add_permission(request)
    
    def has_change_permission(self, request, obj=None):
        """Agents can only change their own users"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            if obj is None:
                return True
            # Agent can only edit users that belong to them
            return obj.agent == request.user
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Agents cannot delete users"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Automatically assign agent when agent creates a user"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not change:
            # New user created by agent
            obj.agent = request.user
            obj.user_type = 'USER'  # Force user type to be USER
            obj.is_staff = False  # Regular users are not staff
        super().save_model(request, obj, form, change)
    
    # Custom actions
    actions = ['make_agent', 'make_user', 'activate_users', 'deactivate_users']
    
    def get_actions(self, request):
        """Limit actions for agents"""
        actions = super().get_actions(request)
        
        # Agents cannot change user types
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            if 'make_agent' in actions:
                del actions['make_agent']
            if 'make_user' in actions:
                del actions['make_user']
        
        return actions
    
    def make_agent(self, request, queryset):
        updated = queryset.update(user_type='AGENT', is_staff=True)
        self.message_user(request, f'{updated} user(s) have been made agents.')
    make_agent.short_description = "Make selected users Agents"
    
    def make_user(self, request, queryset):
        updated = queryset.update(user_type='USER', is_staff=False)
        self.message_user(request, f'{updated} user(s) have been made normal users.')
    make_user.short_description = "Make selected users Normal Users"
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) have been activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) have been deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(ReferralTracking)
class ReferralTrackingAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'agent', 'created_at']
    list_filter = ['agent', 'created_at']
    search_fields = ['referrer__username', 'referred_user__username', 'agent__username']
    readonly_fields = ['referrer', 'referred_user', 'agent', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # If user is an agent, show only their referral tracking
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return qs.filter(agent=request.user)
        
        return qs
    
    def has_module_permission(self, request):
        """Hide ReferralTracking from agents completely"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False  # Agents cannot see this model at all
        return super().has_module_permission(request)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
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
        # Show referral count
        return qs.select_related('referred_by', 'agent')
    
    # Custom action to create agent
    actions = ['make_agent', 'make_user', 'activate_users', 'deactivate_users']
    
    def make_agent(self, request, queryset):
        queryset.update(user_type='AGENT')
        self.message_user(request, f'{queryset.count()} users have been made agents.')
    make_agent.short_description = "Make selected users Agents"
    
    def make_user(self, request, queryset):
        queryset.update(user_type='USER')
        self.message_user(request, f'{queryset.count()} users have been made normal users.')
    make_user.short_description = "Make selected users Normal Users"
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} users have been activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} users have been deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(ReferralTracking)
class ReferralTrackingAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'agent', 'created_at']
    list_filter = ['agent', 'created_at']
    search_fields = ['referrer__username', 'referred_user__username', 'agent__username']
    readonly_fields = ['referrer', 'referred_user', 'agent', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        # Prevent manual creation
        return False
    
    def has_change_permission(self, request, obj=None):
        # Make it read-only
        return False
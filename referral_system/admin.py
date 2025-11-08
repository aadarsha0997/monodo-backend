from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, ReferralTracking, Record, Level, LevelUpgrade, LevelAssignment


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = [
        'username',
        'phone_number',
        'user_type',
        'level',
        'referral_code',
        'referred_by',
        'agent',
        'is_active',
        'date_joined',
    ]
    list_filter = ['user_type', 'level', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'phone_number', 'referral_code']
    ordering = ['-date_joined']
    autocomplete_fields = ['referred_by', 'agent', 'level']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('phone_number', 'withdraw_password')
        }),
        ('User Type & Referral', {
            'fields': ('user_type', 'level', 'referral_code', 'referred_by', 'agent')
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
            'fields': (
                'username',
                'phone_number',
                'password1',
                'password2',
                'withdraw_password',
                'user_type',
                'level',
                'referred_by',
                'agent',
            ),
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


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'price', 'commission', 'total_value', 'status', 'created_at', 'created_by', 'completed_at']
    list_filter = ['level', 'status', 'created_at', 'completed_at']
    search_fields = ['title', 'description', 'level__display_name']
    readonly_fields = ['id', 'total_value', 'created_at', 'updated_at', 'completed_at']
    ordering = ['level__level_order', 'title']
    autocomplete_fields = ['level', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'level', 'created_by', 'title', 'description', 'image')
        }),
        ('Financial Details', {
            'fields': ('price', 'commission', 'commission_percentage', 'total_value')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('level', 'created_by')


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'commission_rate', 'image_upload_limit', 'is_active', 'level_order']
    list_filter = ['is_active']
    search_fields = ['display_name', 'name']
    ordering = ['level_order']


@admin.register(LevelUpgrade)
class LevelUpgradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'from_level', 'to_level', 'amount_paid', 'payment_method', 'upgraded_at']
    list_filter = ['payment_method', 'upgraded_at']
    search_fields = ['user__username', 'from_level__display_name', 'to_level__display_name', 'transaction_id']
    readonly_fields = ['upgraded_at']
    ordering = ['-upgraded_at']


@admin.register(LevelAssignment)
class LevelAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'assigned_by', 'from_level', 'to_level', 'assigned_at']
    list_filter = ['assigned_at', 'assigned_by__user_type']
    search_fields = ['user__username', 'assigned_by__username', 'from_level__display_name', 'to_level__display_name']
    readonly_fields = ['assigned_at']
    ordering = ['-assigned_at']


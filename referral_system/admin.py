from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, ReferralTracking, Record, Level, LevelUpgrade, LevelAssignment, LoginActivity, Review
from django.urls import path, reverse
from django.shortcuts import render
from django.utils.html import format_html
from .models import CustomUser, ReferralTracking


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
    
    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if hasattr(request.user, 'user_type') and request.user.user_type in {'SUPERADMIN', 'AGENT'}:
            display = [field for field in display if field != 'level']
        return display

    def get_urls(self):
        """Add custom URL for agent profile"""
        urls = super().get_urls()
        custom_urls = [
            path('my-profile/', self.admin_site.admin_view(self.agent_profile_view), name='referral_system_customuser_myprofile'),
        ]
        return custom_urls + urls
    
    def agent_profile_view(self, request):
        """Custom view for agent to see their own profile"""
        agent = request.user
        
        # Count total referred users
        total_users = CustomUser.objects.filter(agent=agent).count()
        
        context = {
            **self.admin_site.each_context(request),
            'agent': agent,
            'total_users': total_users,
            'title': 'My Profile',
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
            'has_permission': True,
        }
        
        return render(request, 'admin/agent_profile.html', context)
    
    def changelist_view(self, request, extra_context=None):
        """Add message at the top for agents"""
        extra_context = extra_context or {}
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            # Add a message with profile link
            from django.contrib import messages
            profile_url = reverse('admin:referral_system_customuser_myprofile')
            message = format_html(
                '👤 <strong>Welcome, {}!</strong> Your Referral Code: <strong>{}</strong> | '
                '<a href="{}" style="color: #fff; text-decoration: underline;">View Full Profile</a>',
                request.user.username,
                request.user.referral_code,
                profile_url
            )
            messages.info(request, message)
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # If user is an agent (not superuser), show ONLY their users
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return qs.filter(agent=request.user).select_related('referred_by', 'agent')
        
        # Superadmins see all users
        return qs.select_related('referred_by', 'agent')
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on user type"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
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
        fieldsets = super().get_fieldsets(request, obj)
        if hasattr(request.user, 'user_type') and request.user.user_type in {'SUPERADMIN', 'AGENT'}:
            fieldsets = self._remove_field_from_fieldsets(fieldsets, 'level')
        return fieldsets

    def get_add_fieldsets(self, request):
        fieldsets = super().get_add_fieldsets(request)
        if hasattr(request.user, 'user_type') and request.user.user_type in {'SUPERADMIN', 'AGENT'}:
            fieldsets = self._remove_field_from_fieldsets(fieldsets, 'level')
        return fieldsets

    @staticmethod
    def _remove_field_from_fieldsets(fieldsets, field_name):
        new_fieldsets = []
        for name, options in fieldsets:
            fields = options.get('fields')
            if isinstance(fields, (list, tuple)):
                filtered = [f for f in fields if f != field_name]
                options = {**options, 'fields': filtered if isinstance(fields, list) else tuple(filtered)}
            new_fieldsets.append((name, options))
        return tuple(new_fieldsets)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only for agents"""
        readonly = list(self.readonly_fields)
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            readonly.extend(['username', 'agent', 'referred_by'])
            if obj:
                readonly.append('user_type')
        
        return readonly
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form for agents"""
        form = super().get_form(request, obj, **kwargs)
        if hasattr(request.user, 'user_type') and request.user.user_type in {'SUPERADMIN', 'AGENT'}:
            form.base_fields.pop('level', None)
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            if 'referred_by' in form.base_fields:
                from django.db.models import Q
                form.base_fields['referred_by'].queryset = CustomUser.objects.filter(
                    Q(id=request.user.id) | Q(agent=request.user)
                )
        
        return form
    
    def has_add_permission(self, request):
        """Agents can add new users"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT':
            return True
        return super().has_add_permission(request)
    
    def has_change_permission(self, request, obj=None):
        """Agents can only change their users"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            if obj is None:
                return True
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
            obj.agent = request.user
            obj.user_type = 'USER'
            obj.is_staff = False
        super().save_model(request, obj, form, change)
    
    actions = ['make_agent', 'make_user', 'activate_users', 'deactivate_users']
    
    def get_actions(self, request):
        """Limit actions for agents"""
        actions = super().get_actions(request)
        
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
        
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return qs.filter(agent=request.user)
        
        return qs
    
    def has_module_permission(self, request):
        """Hide ReferralTracking from agents completely"""
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False
        return super().has_module_permission(request)
    
    def has_add_permission(self, request):
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
    filter_horizontal = ['reviews']
    
    fieldsets = (
    ('Basic Information', {
        'fields': ('id', 'level', 'created_by', 'title', 'description', 'image', 'reviews')
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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['short_review', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['review_text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def short_review(self, obj):
        snippet = obj.review_text[:50]
        return f"{snippet}..." if len(obj.review_text) > 50 else snippet
    short_review.short_description = 'Review Snippet'


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'ip_address',
        'browser',
        'operating_system',
        'device_type',
        'login_time',
    ]
    list_filter = ['device_type', 'browser', 'operating_system', 'login_time']
    search_fields = ['user__username', 'ip_address', 'browser', 'operating_system', 'user_agent']
    readonly_fields = [
        'user',
        'login_time',
        'ip_address',
        'location',
        'user_agent',
        'browser',
        'operating_system',
        'device_type',
        'accept_language',
        'session_key',
        'referrer',
        'device_time',
        'extra_metadata',
    ]
    ordering = ['-login_time']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def has_module_permission(self, request):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False
        return super().has_module_permission(request)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'commission_rate', 'image_upload_limit', 'is_active', 'level_order']
    list_filter = ['is_active']
    search_fields = ['display_name', 'name']
    ordering = ['level_order']

    def has_module_permission(self, request):
        user_type = getattr(request.user, 'user_type', None)
        if request.user.is_superuser or user_type == 'SUPERADMIN':
            return True
        return False


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

    
    def has_delete_permission(self, request, obj=None):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

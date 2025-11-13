from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, ReferralTracking, Record, Level, LevelUpgrade, LevelAssignment, LoginActivity, Review
from django.urls import path, reverse
from django.shortcuts import render
from django.utils.html import format_html
from .models import CustomUser, ReferralTracking


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username',
            'phone_number',
            'withdraw_password',
            'user_type',
            'level',
            'balance',
            'referred_by',
            'agent',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['balance'].initial = self.fields['balance'].initial or CustomUser._meta.get_field('balance').default
        self.fields['withdraw_password'].help_text = "This is the secondary password used for withdrawals."
        self.fields['withdraw_password'].required = True


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = [
        'id',
        'username',
        'superior_id',
        'phone_number',
        'balance_amount',
        'available_daily_order',
        'taking_orders_today',
        'todays_commission',
        'credibility_score',
        'superior_user',
        'invitation_code',
        'status_display',
        'membership_level',
        'frozen_amount',
        'allow_withdrawal',
        'registration_time',
        'last_login_time',
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
        ('Membership & Referral', {
            'fields': (
                'user_type',
                'level',
                'balance',
                'taking_orders_today',
                'referral_code',
                'referred_by',
                'agent'
            )
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
                'balance',
                'referred_by',
                'agent',
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if hasattr(request.user, 'user_type') and request.user.user_type in {'SUPERADMIN', 'AGENT'}:
            display = [field for field in display if field != 'membership_level']
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
        if request.user.is_superuser:
            return self.fieldsets

        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return (
                (None, {
                    'fields': ('username',)
                }),
                ('Personal Info', {
                    'fields': ('phone_number', 'withdraw_password')
                }),
                ('Referral Info', {
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

    def get_add_fieldsets(self, request):
        fieldsets = super().get_add_fieldsets(request)
        if request.user.is_superuser:
            return self.add_fieldsets

        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            return (
                (None, {
                    'classes': ('wide',),
                    'fields': (
                        'username',
                        'phone_number',
                        'password1',
                        'password2',
                        'withdraw_password',
                    ),
                }),
            )

        return super().get_add_fieldsets(request)

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
        if request.user.is_superuser:
            return ['last_login']

        readonly = list(self.readonly_fields)

        if hasattr(request.user, 'user_type') and request.user.user_type == 'AGENT' and not request.user.is_superuser:
            readonly.extend(['username', 'agent', 'referred_by'])
            if obj:
                readonly.append('user_type')
        
        return readonly
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form for agents"""
        form = super().get_form(request, obj, **kwargs)
        
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

    # --- Custom list display helpers ---
    def superior_id(self, obj):
        return obj.agent_id or obj.referred_by_id or '—'

    superior_id.short_description = 'Superior ID'

    def balance_amount(self, obj):
        balance = getattr(obj, 'balance', None)
        if balance is None:
            return '—'
        return balance

    balance_amount.short_description = 'Balance'

    def available_daily_order(self, obj):
        value = getattr(obj, 'available_daily_order', None)
        if value is None:
            return '—'
        return value

    available_daily_order.short_description = 'Available for daily order'

    def taking_orders_today(self, obj):
        value = getattr(obj, 'taking_orders_today', None)
        if value is None:
            return '—'
        return 'Yes' if value else 'No'

    taking_orders_today.short_description = 'Taking orders today'

    def todays_commission(self, obj):
        commission = getattr(obj, 'todays_commission', None)
        if commission is None:
            return '—'
        return commission

    todays_commission.short_description = "Today's commission"

    def credibility_score(self, obj):
        credibility = getattr(obj, 'credibility', None)
        if credibility is None:
            return '—'
        return credibility

    credibility_score.short_description = 'Credibility'

    def superior_user(self, obj):
        if obj.agent:
            return obj.agent
        if obj.referred_by:
            return obj.referred_by
        return '—'

    superior_user.short_description = 'Superior user'

    def invitation_code(self, obj):
        return obj.referral_code or '—'

    invitation_code.short_description = 'Invitation code'

    def status_display(self, obj):
        return 'Active' if obj.is_active else 'Inactive'

    status_display.short_description = 'Status'

    def membership_level(self, obj):
        return obj.level.display_name if obj.level else '—'

    membership_level.short_description = 'Membership Level'

    def frozen_amount(self, obj):
        frozen = getattr(obj, 'frozen_amount', None)
        if frozen is None:
            return '—'
        return frozen

    frozen_amount.short_description = 'Frozen Amount'

    def allow_withdrawal(self, obj):
        allow = getattr(obj, 'allow_withdrawal', None)
        if allow is None:
            return 'Yes' if obj.is_active else 'No'
        return 'Yes' if allow else 'No'

    allow_withdrawal.short_description = 'Allow Withdrawal'

    def registration_time(self, obj):
        return obj.date_joined

    registration_time.short_description = 'Registration time'

    def last_login_time(self, obj):
        return obj.last_login

    last_login_time.short_description = 'Last login time'


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
    list_display = [
        'id',
        'level_name',
        'default_status',
        'commission_rate',
        'minimum_balance',
        'orders_received_total',
        'withdrawals_total',
        'minimum_withdrawal',
        'maximum_withdrawal',
    ]
    list_filter = ['is_active']
    search_fields = ['display_name', 'name']
    ordering = ['level_order']

    def level_name(self, obj):
        return obj.display_name

    level_name.short_description = 'Name'

    def default_status(self, obj):
        return obj.is_default

    default_status.boolean = True
    default_status.short_description = 'Default'

    def orders_received_total(self, obj):
        return obj.orders_received_count

    orders_received_total.short_description = 'Number of order received'

    def withdrawals_total(self, obj):
        return obj.withdrawals_count

    withdrawals_total.short_description = 'Number of withdrawals'

    def minimum_withdrawal(self, obj):
        return obj.min_withdraw_amount

    minimum_withdrawal.short_description = 'Minimum amount to withdraw'

    def maximum_withdrawal(self, obj):
        return obj.max_withdraw_amount

    maximum_withdrawal.short_description = 'Maximum withdrawal amount'

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

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from decimal import Decimal, InvalidOperation
from .models import CustomUser, ReferralTracking, Record, Level, LevelUpgrade, LevelAssignment, LoginActivity, Review, UserProduct


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        help_text="Required. Must be unique."
    )
    withdraw_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        required=True,
        help_text="This is the secondary password used for withdrawals.",
        label="Withdrawal Password"
    )
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'phone_number', 'user_type', 'level', 'agent', 'referred_by', 'referral_code', 
                  'balance', 'available_daily_order', 'taking_orders_today', 'todays_commission', 
                  'credibility', 'frozen_amount', 'allow_withdrawal', 'rob_single', 'operate', 'place', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set agent queryset
        if 'agent' in self.fields:
            self.fields['agent'].queryset = CustomUser.objects.filter(user_type='AGENT')
            self.fields['agent'].required = False
            self.fields['agent'].empty_label = "(None)"
        
        # Set defaults for optional fields
        if 'user_type' in self.fields:
            self.fields['user_type'].initial = 'USER'
            self.fields['user_type'].required = False
        if 'balance' in self.fields:
            self.fields['balance'].initial = 20.00
            self.fields['balance'].required = False
        if 'taking_orders_today' in self.fields:
            self.fields['taking_orders_today'].initial = 0
            self.fields['taking_orders_today'].required = False
        if 'available_daily_order' in self.fields:
            self.fields['available_daily_order'].initial = 0
            self.fields['available_daily_order'].required = False
        if 'todays_commission' in self.fields:
            self.fields['todays_commission'].initial = 0.00
            self.fields['todays_commission'].required = False
        if 'credibility' in self.fields:
            self.fields['credibility'].initial = 100
            self.fields['credibility'].required = False
        if 'frozen_amount' in self.fields:
            self.fields['frozen_amount'].initial = 0.00
            self.fields['frozen_amount'].required = False
        if 'allow_withdrawal' in self.fields:
            self.fields['allow_withdrawal'].initial = True
            self.fields['allow_withdrawal'].required = False
        if 'rob_single' in self.fields:
            self.fields['rob_single'].initial = False
            self.fields['rob_single'].required = False
        if 'is_active' in self.fields:
            self.fields['is_active'].initial = True
            self.fields['is_active'].required = False
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set withdraw_password - use provided value or default to password1
        withdraw_pwd = self.cleaned_data.get('withdraw_password', '')
        if not withdraw_pwd:
            withdraw_pwd = self.cleaned_data.get('password1', '')
        user.withdraw_password = withdraw_pwd
        
        # Set default values if not provided
        if not user.user_type:
            user.user_type = 'USER'
        if not user.balance:
            user.balance = 20.00
        if user.taking_orders_today is None:
            user.taking_orders_today = 0
        if user.available_daily_order is None:
            user.available_daily_order = 0
        if user.todays_commission is None:
            user.todays_commission = 0.00
        if user.credibility is None:
            user.credibility = 100
        if user.frozen_amount is None:
            user.frozen_amount = 0.00
        if user.allow_withdrawal is None:
            user.allow_withdrawal = True
        if user.rob_single is None:
            user.rob_single = False
        if user.is_active is None:
            user.is_active = True
        
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    
    # Display all requested fields in the exact order specified
    list_display = [
        'id',
        'username',
        'superior_id',
        'phone_number',
        'balance_display',
        'available_daily_order',
        'taking_orders_today',
        'current_orders_made',
        'orders_received_today',
        'todays_commission',
        'credibility',
        'superior_user',
        'invitation_code',
        'status_display',
        'membership_level',
        'frozen_amount',
        'rob_single',
        'allow_withdrawal',
        'registration_time',
        'last_login_time',
        'add_debit_button',
        'setup_orders_button',
        'reset_order_quantity_button',
        'more_actions_button',
    ]
    
    list_filter = ['user_type', 'level', 'is_active', 'is_staff', 'allow_withdrawal', 'rob_single', 'date_joined']
    search_fields = ['username', 'phone_number', 'referral_code', 'agent__username']
    ordering = ['-date_joined']
    autocomplete_fields = ['agent', 'level', 'referred_by']
    
    # Custom display methods
    def balance_display(self, obj):
        """Display balance with red color and animation if negative"""
        balance = obj.balance or 0
        if balance < 0:
            return format_html(
                '<span class="negative-balance" style="color: red; font-weight: bold; padding: 2px 6px; border-radius: 3px; display: inline-block; animation: pulseRed 2s infinite;">${}</span>',
                balance
            )
        return f"${balance}"
    balance_display.short_description = 'Balance'
    balance_display.admin_order_field = 'balance'
    
    def superior_id(self, obj):
        """Display agent/superior ID"""
        return obj.agent_id if obj.agent_id else '—'
    superior_id.short_description = 'Superior ID'
    
    def superior_user(self, obj):
        """Display agent/superior username"""
        return obj.agent.username if obj.agent else '—'
    superior_user.short_description = 'Superior User'
    
    def invitation_code(self, obj):
        """Display referral code"""
        return obj.referral_code if obj.referral_code else '—'
    invitation_code.short_description = 'Invitation Code'
    
    def status_display(self, obj):
        """Display status as Active/Inactive"""
        return 'Active' if obj.is_active else 'Inactive'
    status_display.short_description = 'Status'
    
    def membership_level(self, obj):
        """Display membership level"""
        return obj.level.get_name_display() if obj.level else '—'
    membership_level.short_description = 'Membership Level'
    
    def registration_time(self, obj):
        """Display registration time"""
        return obj.date_joined
    registration_time.short_description = 'Registration Time'
    
    def last_login_time(self, obj):
        """Display last login time"""
        return obj.last_login if obj.last_login else '—'
    last_login_time.short_description = 'Last Login Time'
    
    def save_model(self, request, obj, form, change):
        """Set withdraw_password from form if provided and ensure available_daily_order matches level"""
        if not change and hasattr(form, 'cleaned_data'):
            if 'withdraw_password' in form.cleaned_data:
                obj.withdraw_password = form.cleaned_data['withdraw_password']
        
        # Ensure available_daily_order matches level's orders_received_count
        # This ensures it's set correctly even if form field is manually edited
        if hasattr(form, 'cleaned_data') and 'level' in form.cleaned_data:
            level = form.cleaned_data.get('level')
            if level and hasattr(level, 'orders_received_count'):
                # Always update available_daily_order to match level's orders_received_count
                # when level is set (for new users) or changed (for existing users)
                if not change:
                    # New user - always set it
                    obj.available_daily_order = level.orders_received_count
                elif change:
                    # Existing user - only update if level changed
                    try:
                        old_obj = self.model.objects.get(pk=obj.pk)
                        if old_obj.level != level:
                            obj.available_daily_order = level.orders_received_count
                    except self.model.DoesNotExist:
                        # Fallback: if we can't get old instance, set it anyway
                        obj.available_daily_order = level.orders_received_count
        
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('phone_number', 'withdraw_password')
        }),
        ('User Details', {
            'fields': (
                'user_type',
                'level',
                'agent',
                'referred_by',
                'referral_code',
                'balance',
                'available_daily_order',
                'taking_orders_today',
                'todays_commission',
                'credibility',
                'frozen_amount',
                'allow_withdrawal',
                'rob_single',
                'operate',
                'place',
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
                'agent',
                'referred_by',
                'referral_code',
                'balance',
                'available_daily_order',
                'taking_orders_today',
                'current_orders_made',
                'orders_received_today',
                'start_continuous_orders_after',
                'todays_commission',
                'credibility',
                'frozen_amount',
                'allow_withdrawal',
                'rob_single',
                'operate',
                'place',
                'is_active',
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist to enable real-time updates"""
        response = super().changelist_view(request, extra_context)
        if hasattr(response, 'context_data'):
            response.context_data['enable_realtime_updates'] = True
        return response
    
    class Media:
        js = ('admin/js/add_debit_modal.js', 'admin/js/reset_order_quantity.js', 'admin/js/more_actions_dropdown.js', 'admin/js/account_details_modal.js', 'admin/js/account_change_modal.js', 'admin/js/wallet_information_modal.js', 'admin/js/edit_user_modal.js', 'admin/js/user_level_autofill.js', 'admin/js/realtime_user_stats.js',)
        css = {
            'all': ('admin/css/add_debit_modal.css', 'admin/css/negative_balance.css', 'admin/css/more_actions_dropdown.css',)
        }
    
    def get_urls(self):
        """Add custom URLs for action buttons"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/add-debit/',
                self.admin_site.admin_view(self.add_debit_view),
                name='referral_system_customuser_adddebit',
            ),
            path(
                '<int:user_id>/setup-orders/',
                self.admin_site.admin_view(self.setup_orders_view),
                name='referral_system_customuser_setuporders',
            ),
            path(
                '<int:user_id>/setup-orders/stats/',
                self.admin_site.admin_view(self.setup_orders_stats_view),
                name='referral_system_customuser_setuporders_stats',
            ),
            path(
                '<int:user_id>/reset-order-quantity/',
                self.admin_site.admin_view(self.reset_order_quantity_view),
                name='referral_system_customuser_resetorderquantity',
            ),
            path(
                '<int:user_id>/more-actions/',
                self.admin_site.admin_view(self.more_actions_view),
                name='referral_system_customuser_moreactions',
            ),
            path(
                '<int:user_id>/account-details/',
                self.admin_site.admin_view(self.account_details_view),
                name='referral_system_customuser_accountdetails',
            ),
            path(
                '<int:user_id>/account-change/',
                self.admin_site.admin_view(self.account_change_view),
                name='referral_system_customuser_accountchange',
            ),
            path(
                '<int:user_id>/wallet-information/',
                self.admin_site.admin_view(self.wallet_information_view),
                name='referral_system_customuser_walletinformation',
            ),
            path(
                '<int:user_id>/edit-user/',
                self.admin_site.admin_view(self.edit_user_view),
                name='referral_system_customuser_edituser',
            ),
            path(
                '<int:user_id>/dealing-history/',
                self.admin_site.admin_view(self.dealing_history_view),
                name='referral_system_customuser_dealinghistory',
            ),
            path(
                'level/<int:level_id>/get-orders-count/',
                self.admin_site.admin_view(self.get_level_orders_count),
                name='referral_system_level_get_orders_count',
            ),
            path(
                'get-user-stats/',
                self.admin_site.admin_view(self.get_user_stats_view),
                name='referral_system_customuser_getstats',
            ),
        ]
        return custom_urls + urls
    
    def get_level_orders_count(self, request, level_id):
        """API endpoint to get level's orders_received_count for JavaScript"""
        from django.http import JsonResponse
        try:
            from .models import Level
            level = Level.objects.get(pk=level_id)
            return JsonResponse({
                'orders_received_count': level.orders_received_count,
                'level_name': level.get_name_display(),
            })
        except Level.DoesNotExist:
            return JsonResponse({'error': 'Level not found'}, status=404)
    
    def get_user_stats_view(self, request):
        """API endpoint to get user stats for real-time updates"""
        from django.http import JsonResponse
        user_ids = request.GET.getlist('user_ids[]')
        
        if not user_ids:
            return JsonResponse({'error': 'No user IDs provided'}, status=400)
        
        try:
            user_ids_int = [int(uid) for uid in user_ids]
            users = CustomUser.objects.filter(pk__in=user_ids_int).values(
                'id',
                'available_daily_order',
                'taking_orders_today',
                'current_orders_made',
                'orders_received_today',
                'todays_commission',
                'balance',
                'frozen_amount'
            )
            
            stats = {}
            for user in users:
                stats[str(user['id'])] = {
                    'available_daily_order': user['available_daily_order'] or 0,
                    'taking_orders_today': user['taking_orders_today'] or 0,
                    'current_orders_made': user['current_orders_made'] or 0,
                    'orders_received_today': user['orders_received_today'] or 0,
                    'todays_commission': str(user['todays_commission'] or 0),
                    'balance': str(user['balance'] or 0),
                    'frozen_amount': str(user['frozen_amount'] or 0),
                }
            
            return JsonResponse({'stats': stats})
        except (ValueError, CustomUser.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def add_debit_button(self, obj):
        """Display Add Debit button with blood red color - opens modal"""
        if obj.pk:
            url = reverse('admin:referral_system_customuser_adddebit', args=[obj.pk])
            return format_html(
                '<a href="{}" onclick="event.preventDefault(); openDebitModal({}, \'{}\'); return false;" style="background-color: #8B0000; color: white !important; padding: 2px 6px; text-decoration: none; border-radius: 2px; font-size: 10px; font-weight: 600; display: inline-block; white-space: nowrap; cursor: pointer;">Add Debit</a>',
                url, obj.pk, obj.username
            )
        return '-'
    add_debit_button.short_description = 'Add Debit'
    
    def setup_orders_button(self, obj):
        """Display Setup Orders button with blue color"""
        if obj.pk:
            url = reverse('admin:referral_system_customuser_setuporders', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background-color: #007bff; color: white !important; padding: 2px 6px; text-decoration: none; border-radius: 2px; font-size: 10px; font-weight: 600; display: inline-block; white-space: nowrap;">Setup Orders</a>',
                url
            )
        return '-'
    setup_orders_button.short_description = 'Setup Orders'
    
    def reset_order_quantity_button(self, obj):
        """Display Reset Order Quantity button with orange color - opens modal"""
        if obj.pk:
            url = reverse('admin:referral_system_customuser_resetorderquantity', args=[obj.pk])
            return format_html(
                '<a href="{}" onclick="event.preventDefault(); openResetOrderModal({}, \'{}\'); return false;" style="background-color: #ff8c00; color: white !important; padding: 2px 6px; text-decoration: none; border-radius: 2px; font-size: 10px; font-weight: 600; display: inline-block; white-space: nowrap; cursor: pointer;">Reset Order Qty</a>',
                url, obj.pk, obj.username
            )
        return '-'
    reset_order_quantity_button.short_description = 'Reset Qty'
    
    def more_actions_button(self, obj):
        """Display More Actions button with dropdown menu on hover"""
        if obj.pk:
            user_id = obj.pk
            change_url = reverse('admin:referral_system_customuser_change', args=[obj.pk])
            return format_html(
                '<div class="more-actions-dropdown" style="position: relative; display: inline-block;">'
                '<a href="#" class="more-actions-btn" style="background-color: #6c757d; color: white !important; padding: 2px 6px; text-decoration: none; border-radius: 2px; font-size: 10px; font-weight: 600; display: inline-block; white-space: nowrap; cursor: pointer;">More actions</a>'
                '<div id="more-actions-menu-{}" class="more-actions-menu" style="display: none; position: absolute; top: 100%; left: 0; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 9999; min-width: 180px; margin-top: 4px; overflow: visible;">'
                '<a href="#" onclick="event.preventDefault(); openWalletInformationModal({}, \'{}\'); return false;" class="dropdown-item" style="display: block; padding: 10px 15px; color: #212529; text-decoration: none; border-bottom: 1px solid #f0f0f0; font-size: 13px; cursor: pointer;"><span style="margin-right: 8px;">&gt;</span> Wallet Information</a>'
                '<a href="#" onclick="event.preventDefault(); openEditUserModal({}, \'{}\'); return false;" class="dropdown-item" style="display: block; padding: 10px 15px; color: #212529; text-decoration: none; border-bottom: 1px solid #f0f0f0; font-size: 13px; cursor: pointer;"><span style="margin-right: 8px;">&gt;</span> Edit</a>'
                '<a href="#" onclick="event.preventDefault(); openAccountChangeModal({}, \'{}\'); return false;" class="dropdown-item" style="display: block; padding: 10px 15px; color: #212529; text-decoration: none; border-bottom: 1px solid #f0f0f0; font-size: 13px; cursor: pointer;"><span style="margin-right: 8px;">&gt;</span> Account Change</a>'
                '<a href="/admin/referral_system/customuser/{}/dealing-history/" class="dropdown-item" style="display: block; padding: 10px 15px; color: #212529; text-decoration: none; border-bottom: 1px solid #f0f0f0; font-size: 13px;"><span style="margin-right: 8px;">&gt;</span> Dealing History</a>'
                '<a href="#" onclick="event.preventDefault(); openAccountDetailsModal({}, \'{}\'); return false;" class="dropdown-item" style="display: block; padding: 10px 15px; color: #212529; text-decoration: none; font-size: 13px; cursor: pointer;"><span style="margin-right: 8px;">&gt;</span> Account Details</a>'
                '</div>'
                '</div>',
                user_id, user_id, obj.username, user_id, obj.username, user_id, obj.username, user_id, user_id, obj.username
            )
        return '-'
    more_actions_button.short_description = 'More Actions'
    
    def add_debit_view(self, request, user_id):
        """Handle Add Debit action with modal form"""
        from django.shortcuts import render
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            if request.method == 'POST':
                transaction_type = request.POST.get('type')
                amount = request.POST.get('amount')
                remark = request.POST.get('remark', '')
                remark_type = request.POST.get('remark_type', '')
                
                # Validate required fields
                if not transaction_type or not amount:
                    messages.error(request, 'Type and Amount are required fields.')
                    return render(request, 'admin/referral_system/add_debit_modal.html', {
                        'user': user,
                        'opts': self.model._meta,
                        'has_view_permission': self.has_view_permission(request, user),
                    })
                
                try:
                    amount_decimal = Decimal(str(amount))
                    if amount_decimal <= 0:
                        messages.error(request, 'Amount must be greater than 0.')
                        return render(request, 'admin/referral_system/add_debit_modal.html', {
                            'user': user,
                            'opts': self.model._meta,
                            'has_view_permission': self.has_view_permission(request, user),
                        })
                    
                    # Get current balance
                    current_balance = user.balance or Decimal('0.00')
                    
                    # Update user balance based on transaction type
                    if transaction_type == 'debit':
                        # Debit: Subtract from balance
                        new_balance = current_balance - amount_decimal
                        if new_balance < 0:
                            messages.warning(request, f'Warning: Balance will become negative: ${new_balance}')
                        user.balance = new_balance
                        action_msg = 'removed from'
                    elif transaction_type == 'credit':
                        # Credit: Add to balance
                        user.balance = current_balance + amount_decimal
                        action_msg = 'added to'
                    else:
                        messages.error(request, 'Invalid transaction type.')
                        return render(request, 'admin/referral_system/add_debit_modal.html', {
                            'user': user,
                            'opts': self.model._meta,
                            'has_view_permission': self.has_view_permission(request, user),
                        })
                    
                    # Save the updated balance
                    user.save(update_fields=['balance'])
                    
                    # Build remark - use remark_type if provided, otherwise use remark
                    final_remark = remark_type if remark_type else remark
                    if remark_type and remark and remark != remark_type:
                        final_remark = f"{remark_type}: {remark}"
                    
                    messages.success(
                        request, 
                        f'Transaction processed successfully! ${amount_decimal} {action_msg} balance. '
                        f'Previous Balance: ${current_balance} → New Balance: ${user.balance}'
                    )
                    return HttpResponseRedirect(
                        reverse('admin:referral_system_customuser_change', args=[user_id])
                    )
                except (ValueError, InvalidOperation) as e:
                    messages.error(request, f'Invalid amount format: {str(e)}')
                    return render(request, 'admin/referral_system/add_debit_modal.html', {
                        'user': user,
                        'opts': self.model._meta,
                        'has_view_permission': self.has_view_permission(request, user),
                    })
            
            # GET request - show modal
            return render(request, 'admin/referral_system/add_debit_modal.html', {
                'user': user,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            })
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def setup_orders_view(self, request, user_id):
        """Handle Setup Orders - Manage user products/orders with position control"""
        from django.shortcuts import render
        from django.core.paginator import Paginator
        from django.db import transaction
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            # Handle POST requests for adding/removing/updating products
            if request.method == 'POST':
                action = request.POST.get('action')
                
                if action == 'update_settings':
                    # Update user order settings
                    user.current_orders_made = int(request.POST.get('current_orders_made', 0) or 0)
                    user.orders_received_today = int(request.POST.get('orders_received_today', 0) or 0)
                    user.start_continuous_orders_after = int(request.POST.get('start_continuous_orders_after', 0) or 0)
                    user.save(update_fields=['current_orders_made', 'orders_received_today', 'start_continuous_orders_after'])
                    messages.success(request, 'Order settings updated successfully.')
                
                elif action == 'add_product':
                    record_id = request.POST.get('record_id')
                    position = int(request.POST.get('position', 0) or 0)
                    if record_id:
                        try:
                            record = Record.objects.get(pk=record_id)
                            user_product, created = UserProduct.objects.get_or_create(
                                user=user,
                                record=record,
                                defaults={'position': position, 'is_active': True}
                            )
                            if not created:
                                user_product.position = position
                                user_product.is_active = True
                                user_product.save()
                            messages.success(request, f'Product "{record.title}" added successfully.')
                        except Record.DoesNotExist:
                            messages.error(request, 'Record not found.')
                
                elif action == 'remove_product':
                    user_product_id = request.POST.get('user_product_id')
                    if user_product_id:
                        try:
                            user_product = UserProduct.objects.get(pk=user_product_id, user=user)
                            user_product.delete()
                            messages.success(request, 'Product removed successfully.')
                        except UserProduct.DoesNotExist:
                            messages.error(request, 'Product not found.')
                
                elif action == 'update_positions':
                    # Update positions from form data
                    positions = request.POST.getlist('positions[]')
                    for pos_data in positions:
                        if pos_data:
                            parts = pos_data.split(':')
                            if len(parts) == 2:
                                user_product_id, new_position = parts
                                try:
                                    user_product = UserProduct.objects.get(pk=user_product_id, user=user)
                                    user_product.position = int(new_position)
                                    user_product.save(update_fields=['position'])
                                except (UserProduct.DoesNotExist, ValueError):
                                    pass
                    messages.success(request, 'Product positions updated successfully.')
                
                elif action == 'reset_continuous_orders':
                    # Reset continuous orders count
                    user.current_orders_made = 0
                    user.save(update_fields=['current_orders_made'])
                    messages.success(request, 'Continuous orders count reset successfully.')
                
                return HttpResponseRedirect(reverse('admin:referral_system_customuser_setuporders', args=[user_id]))
            
            # GET request - show setup orders page
            # Get user's products ordered by position
            user_products = UserProduct.objects.filter(user=user, is_active=True).select_related('record').order_by('position', 'created_at')
            
            # Get available records for adding (all records, can be filtered)
            all_records = Record.objects.all().select_related('level', 'created_by').order_by('-created_at')
            
            # Get maximum orders from level
            max_orders_by_level = user.level.orders_received_count if user.level else 0
            
            # Filter records by price range if provided
            min_price = request.GET.get('min_price', '')
            max_price = request.GET.get('max_price', '')
            if min_price:
                try:
                    all_records = all_records.filter(price__gte=Decimal(min_price))
                except (ValueError, InvalidOperation):
                    pass
            if max_price:
                try:
                    all_records = all_records.filter(price__lte=Decimal(max_price))
                except (ValueError, InvalidOperation):
                    pass
            
            # Paginate available records for product selection
            paginator = Paginator(all_records, 20)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Create range for tick marks
            max_orders_range = range(1, max_orders_by_level + 1) if max_orders_by_level > 0 else []
            
            return render(request, 'admin/referral_system/setup_orders.html', {
                'user': user,
                'user_products': user_products,
                'available_records': page_obj,
                'max_orders_by_level': max_orders_by_level,
                'max_orders_range': max_orders_range,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            })
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def setup_orders_stats_view(self, request, user_id):
        """AJAX endpoint for real-time order stats"""
        from django.http import JsonResponse
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            max_orders_by_level = user.level.orders_received_count if user.level else 0
            
            return JsonResponse({
                'orders_received_today': user.orders_received_today,
                'taking_orders_today': user.taking_orders_today,
                'max_orders_by_level': max_orders_by_level,
                'progress_percentage': round((user.orders_received_today / max_orders_by_level * 100) if max_orders_by_level > 0 else 0, 2),
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
    def reset_order_quantity_view(self, request, user_id):
        """Handle Reset Order Quantity - Reset all order tracking and balance to default"""
        from django.http import JsonResponse
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            # Store old values for response
            old_balance = user.balance
            old_orders_received = user.orders_received_today
            old_taking_orders = user.taking_orders_today
            old_current_orders = user.current_orders_made
            
            # Reset order tracking fields
            user.orders_received_today = 0
            user.taking_orders_today = 0
            user.current_orders_made = 0
            user.todays_commission = Decimal('0.00')
            
            # Reset balance to default starting balance
            user.balance = Decimal('20.00')
            
            # Save the changes
            user.save(update_fields=[
                'orders_received_today',
                'taking_orders_today',
                'current_orders_made',
                'todays_commission',
                'balance'
            ])
            
            # Return JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                messages.success(
                    request,
                    f'User {user.username} reset successfully! '
                    f'Balance: ${old_balance} → ${user.balance}, '
                    f'Orders Received: {old_orders_received} → 0, '
                    f'Taking Orders: {old_taking_orders} → 0, '
                    f'Current Orders: {old_current_orders} → 0'
                )
                return JsonResponse({
                    'success': True,
                    'message': f'User {user.username} reset successfully!',
                    'new_balance': str(user.balance),
                    'new_orders_received': user.orders_received_today,
                    'new_taking_orders': user.taking_orders_today,
                    'new_current_orders': user.current_orders_made,
                })
            
            # Fallback for non-AJAX requests
            messages.success(
                request,
                f'User {user.username} reset successfully! '
                f'Balance: ${old_balance} → ${user.balance}, '
                f'Orders Received: {old_orders_received} → 0, '
                f'Taking Orders: {old_taking_orders} → 0, '
                f'Current Orders: {old_current_orders} → 0'
            )
            return HttpResponseRedirect(
                reverse('admin:referral_system_customuser_change', args=[user_id])
            )
        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def account_details_view(self, request, user_id):
        """Handle Account Details - Display and edit account details via AJAX"""
        from django.shortcuts import render
        from django.http import JsonResponse
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            if request.method == 'POST':
                # Update account details
                user.username = request.POST.get('username', user.username)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                if hasattr(user, 'email'):
                    user.email = request.POST.get('email', getattr(user, 'email', ''))
                user.operate = request.POST.get('operate', user.operate)
                user.place = request.POST.get('place', user.place)
                user.is_active = request.POST.get('is_active') == 'on'
                
                # Update bank account details if provided
                if 'bank_account_number' in request.POST:
                    user.bank_account_number = request.POST.get('bank_account_number', '')
                if 'bank_account_holder_name' in request.POST:
                    user.bank_account_holder_name = request.POST.get('bank_account_holder_name', '')
                if 'bank_name' in request.POST:
                    user.bank_name = request.POST.get('bank_name', '')
                if 'bank_routing_number' in request.POST:
                    user.bank_routing_number = request.POST.get('bank_routing_number', '')
                if 'bank_account_type' in request.POST:
                    user.bank_account_type = request.POST.get('bank_account_type', 'checking')
                
                user.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Account details updated successfully!'
                    })
                
                messages.success(request, 'Account details updated successfully!')
                return HttpResponseRedirect(
                    reverse('admin:referral_system_customuser_change', args=[user_id])
                )
            
            # GET request - return account details as JSON for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'phone_number': user.phone_number or '',
                    'operate': user.operate or '',
                    'place': user.place or '',
                    'is_active': user.is_active,
                    'bank_account_number': user.bank_account_number or '',
                    'bank_account_holder_name': user.bank_account_holder_name or '',
                    'bank_name': user.bank_name or '',
                    'bank_routing_number': user.bank_routing_number or '',
                    'bank_account_type': user.bank_account_type or 'checking',
                    'balance': str(user.balance),
                    'level': user.level.get_name_display() if user.level else 'No Level',
                    'user_type': user.get_user_type_display(),
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                }
                if hasattr(user, 'email'):
                    user_data['email'] = user.email or ''
                return JsonResponse(user_data)
            
            # Fallback for non-AJAX requests
            return render(request, 'admin/referral_system/account_details.html', {
                'user': user,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            })
        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def account_change_view(self, request, user_id):
        """Handle Account Change - Change account type, agent, level, etc."""
        from django.shortcuts import render
        from django.http import JsonResponse
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            if request.method == 'POST':
                # Update account change fields
                user.user_type = request.POST.get('user_type', user.user_type)
                
                # Update level
                level_id = request.POST.get('level')
                if level_id:
                    try:
                        from .models import Level
                        level = Level.objects.get(pk=level_id)
                        user.level = level
                        # Level change will trigger available_daily_order update in save()
                    except Level.DoesNotExist:
                        pass
                else:
                    user.level = None
                
                # Update agent
                agent_id = request.POST.get('agent')
                if agent_id:
                    try:
                        agent = CustomUser.objects.get(pk=agent_id, user_type='AGENT')
                        user.agent = agent
                    except CustomUser.DoesNotExist:
                        pass
                else:
                    user.agent = None
                
                # Update referred_by
                referred_by_id = request.POST.get('referred_by')
                if referred_by_id:
                    try:
                        referred_by = CustomUser.objects.get(pk=referred_by_id)
                        if referred_by.id != user.id:  # Don't allow self-referral
                            user.referred_by = referred_by
                    except CustomUser.DoesNotExist:
                        pass
                else:
                    user.referred_by = None
                
                # Update permissions and status
                user.is_active = request.POST.get('is_active') == 'on'
                user.allow_withdrawal = request.POST.get('allow_withdrawal') == 'on'
                user.rob_single = request.POST.get('rob_single') == 'on'
                
                # Update credibility and frozen amount
                if 'credibility' in request.POST:
                    try:
                        user.credibility = int(request.POST.get('credibility', 100))
                        if user.credibility < 0:
                            user.credibility = 0
                        elif user.credibility > 100:
                            user.credibility = 100
                    except ValueError:
                        pass
                
                if 'frozen_amount' in request.POST:
                    try:
                        from decimal import Decimal
                        user.frozen_amount = Decimal(request.POST.get('frozen_amount', '0.00'))
                    except (ValueError, TypeError):
                        pass
                
                user.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Account changes saved successfully!'
                    })
                
                messages.success(request, 'Account changes saved successfully!')
                return HttpResponseRedirect(
                    reverse('admin:referral_system_customuser_change', args=[user_id])
                )
            
            # GET request - return account change data as JSON for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from .models import Level
                
                # Get all agents for dropdown
                agents = CustomUser.objects.filter(user_type='AGENT').values('id', 'username')
                
                # Get all levels for dropdown (with display name)
                levels = []
                for level in Level.objects.all():
                    levels.append({
                        'id': level.id,
                        'name': level.get_name_display(),
                    })
                
                # Get all users for referred_by dropdown
                users = CustomUser.objects.all().values('id', 'username')
                
                return JsonResponse({
                    'user_type': user.user_type,
                    'current_level_id': user.level.id if user.level else None,
                    'current_agent_id': user.agent.id if user.agent else None,
                    'current_referred_by_id': user.referred_by.id if user.referred_by else None,
                    'is_active': user.is_active,
                    'allow_withdrawal': user.allow_withdrawal,
                    'rob_single': user.rob_single,
                    'credibility': user.credibility,
                    'frozen_amount': str(user.frozen_amount),
                    'agents': list(agents),
                    'levels': list(levels),
                    'users': list(users),
                })
            
            # Fallback for non-AJAX requests
            return render(request, 'admin/referral_system/account_change.html', {
                'user': user,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            })
        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def wallet_information_view(self, request, user_id):
        """Handle Wallet Information - View and edit wallet details"""
        from django.shortcuts import render
        from django.http import JsonResponse
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            if request.method == 'POST':
                # Update wallet information
                if 'balance' in request.POST:
                    try:
                        from decimal import Decimal
                        user.balance = Decimal(request.POST.get('balance', '0.00'))
                    except (ValueError, TypeError):
                        pass
                
                if 'frozen_amount' in request.POST:
                    try:
                        from decimal import Decimal
                        user.frozen_amount = Decimal(request.POST.get('frozen_amount', '0.00'))
                    except (ValueError, TypeError):
                        pass
                
                if 'credibility' in request.POST:
                    try:
                        user.credibility = int(request.POST.get('credibility', 100))
                        if user.credibility < 0:
                            user.credibility = 0
                        elif user.credibility > 100:
                            user.credibility = 100
                    except ValueError:
                        pass
                
                if 'available_daily_order' in request.POST:
                    try:
                        user.available_daily_order = int(request.POST.get('available_daily_order', 0))
                        if user.available_daily_order < 0:
                            user.available_daily_order = 0
                    except ValueError:
                        pass
                
                user.allow_withdrawal = request.POST.get('allow_withdrawal') == 'on'
                
                user.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Wallet information updated successfully!'
                    })
                
                messages.success(request, 'Wallet information updated successfully!')
                return HttpResponseRedirect(
                    reverse('admin:referral_system_customuser_change', args=[user_id])
                )
            
            # GET request - return wallet information as JSON for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'balance': str(user.balance),
                    'frozen_amount': str(user.frozen_amount),
                    'todays_commission': str(user.todays_commission),
                    'credibility': user.credibility,
                    'available_daily_order': user.available_daily_order,
                    'allow_withdrawal': user.allow_withdrawal,
                })
            
            # Fallback for non-AJAX requests
            return render(request, 'admin/referral_system/wallet_information.html', {
                'user': user,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            })
        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def edit_user_view(self, request, user_id):
        """Handle Edit User - Comprehensive edit modal with all fields"""
        from django.shortcuts import render
        from django.http import JsonResponse
        from django.contrib.auth.hashers import make_password
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            if request.method == 'POST':
                # Update basic information
                user.username = request.POST.get('username', user.username)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                
                # Update email if field exists
                if hasattr(user, 'email'):
                    user.email = request.POST.get('email', getattr(user, 'email', ''))
                
                user.referral_code = request.POST.get('referral_code', user.referral_code)
                user.operate = request.POST.get('operate', user.operate)
                user.place = request.POST.get('place', user.place)
                
                # Update account settings
                user.user_type = request.POST.get('user_type', user.user_type)
                
                # Update level
                level_id = request.POST.get('level')
                if level_id:
                    try:
                        from .models import Level
                        level = Level.objects.get(pk=level_id)
                        user.level = level
                    except Level.DoesNotExist:
                        pass
                else:
                    user.level = None
                
                # Update agent
                agent_id = request.POST.get('agent')
                if agent_id:
                    try:
                        agent = CustomUser.objects.get(pk=agent_id, user_type='AGENT')
                        user.agent = agent
                    except CustomUser.DoesNotExist:
                        pass
                else:
                    user.agent = None
                
                # Update referred_by
                referred_by_id = request.POST.get('referred_by')
                if referred_by_id:
                    try:
                        referred_by = CustomUser.objects.get(pk=referred_by_id)
                        if referred_by.id != user.id:
                            user.referred_by = referred_by
                    except CustomUser.DoesNotExist:
                        pass
                else:
                    user.referred_by = None
                
                # Update balance & financial
                if 'balance' in request.POST:
                    try:
                        from decimal import Decimal
                        user.balance = Decimal(request.POST.get('balance', '0.00'))
                    except (ValueError, TypeError):
                        pass
                
                if 'frozen_amount' in request.POST:
                    try:
                        from decimal import Decimal
                        user.frozen_amount = Decimal(request.POST.get('frozen_amount', '0.00'))
                    except (ValueError, TypeError):
                        pass
                
                if 'todays_commission' in request.POST:
                    try:
                        from decimal import Decimal
                        user.todays_commission = Decimal(request.POST.get('todays_commission', '0.00'))
                    except (ValueError, TypeError):
                        pass
                
                if 'credibility' in request.POST:
                    try:
                        user.credibility = int(request.POST.get('credibility', 100))
                        if user.credibility < 0:
                            user.credibility = 0
                        elif user.credibility > 100:
                            user.credibility = 100
                    except ValueError:
                        pass
                
                user.allow_withdrawal = request.POST.get('allow_withdrawal') == 'on'
                
                # Update order tracking
                if 'available_daily_order' in request.POST:
                    try:
                        user.available_daily_order = int(request.POST.get('available_daily_order', 0))
                        if user.available_daily_order < 0:
                            user.available_daily_order = 0
                    except ValueError:
                        pass
                
                if 'taking_orders_today' in request.POST:
                    try:
                        user.taking_orders_today = int(request.POST.get('taking_orders_today', 0))
                        if user.taking_orders_today < 0:
                            user.taking_orders_today = 0
                    except ValueError:
                        pass
                
                if 'orders_received_today' in request.POST:
                    try:
                        user.orders_received_today = int(request.POST.get('orders_received_today', 0))
                        if user.orders_received_today < 0:
                            user.orders_received_today = 0
                    except ValueError:
                        pass
                
                if 'current_orders_made' in request.POST:
                    try:
                        user.current_orders_made = int(request.POST.get('current_orders_made', 0))
                        if user.current_orders_made < 0:
                            user.current_orders_made = 0
                    except ValueError:
                        pass
                
                if 'start_continuous_orders_after' in request.POST:
                    try:
                        user.start_continuous_orders_after = int(request.POST.get('start_continuous_orders_after', 0))
                        if user.start_continuous_orders_after < 0:
                            user.start_continuous_orders_after = 0
                    except ValueError:
                        pass
                
                # Update bank account details
                user.bank_account_holder_name = request.POST.get('bank_account_holder_name', user.bank_account_holder_name)
                user.bank_account_number = request.POST.get('bank_account_number', user.bank_account_number)
                user.bank_name = request.POST.get('bank_name', user.bank_name)
                user.bank_routing_number = request.POST.get('bank_routing_number', user.bank_routing_number)
                user.bank_account_type = request.POST.get('bank_account_type', user.bank_account_type)
                
                # Update permissions & status
                user.is_active = request.POST.get('is_active') == 'on'
                user.is_staff = request.POST.get('is_staff') == 'on'
                user.rob_single = request.POST.get('rob_single') == 'on'
                
                # Update passwords if provided
                password = request.POST.get('password', '').strip()
                if password:
                    user.set_password(password)
                
                withdraw_password = request.POST.get('withdraw_password', '').strip()
                if withdraw_password:
                    user.withdraw_password = make_password(withdraw_password)
                
                user.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'User updated successfully!'
                    })
                
                messages.success(request, 'User updated successfully!')
                return HttpResponseRedirect(
                    reverse('admin:referral_system_customuser_change', args=[user_id])
                )
            
            # GET request - return user data as JSON for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from .models import Level
                
                # Get all agents for dropdown
                agents = CustomUser.objects.filter(user_type='AGENT').values('id', 'username')
                
                # Get all levels for dropdown
                levels = []
                for level in Level.objects.all():
                    levels.append({
                        'id': level.id,
                        'name': level.get_name_display(),
                    })
                
                # Get all users for referred_by dropdown
                users = CustomUser.objects.all().values('id', 'username')
                
                user_data = {
                    'username': user.username,
                    'phone_number': user.phone_number,
                    'referral_code': user.referral_code or '',
                    'operate': user.operate or '',
                    'place': user.place or '',
                    'user_type': user.user_type,
                    'level_id': user.level.id if user.level else None,
                    'agent_id': user.agent.id if user.agent else None,
                    'referred_by_id': user.referred_by.id if user.referred_by else None,
                    'balance': str(user.balance),
                    'frozen_amount': str(user.frozen_amount),
                    'todays_commission': str(user.todays_commission),
                    'credibility': user.credibility,
                    'allow_withdrawal': user.allow_withdrawal,
                    'available_daily_order': user.available_daily_order,
                    'taking_orders_today': user.taking_orders_today,
                    'orders_received_today': user.orders_received_today,
                    'current_orders_made': user.current_orders_made,
                    'start_continuous_orders_after': user.start_continuous_orders_after,
                    'bank_account_holder_name': user.bank_account_holder_name or '',
                    'bank_account_number': user.bank_account_number or '',
                    'bank_name': user.bank_name or '',
                    'bank_routing_number': user.bank_routing_number or '',
                    'bank_account_type': user.bank_account_type or '',
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'rob_single': user.rob_single,
                    'agents': list(agents),
                    'levels': list(levels),
                    'users': list(users),
                }
                
                # Add email if field exists
                if hasattr(user, 'email'):
                    user_data['has_email'] = True
                    user_data['email'] = user.email or ''
                else:
                    user_data['has_email'] = False
                
                return JsonResponse(user_data)
            
            # Fallback for non-AJAX requests
            return render(request, 'admin/referral_system/edit_user.html', {
                'user': user,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            })
        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def dealing_history_view(self, request, user_id):
        """Handle Dealing History - Show all records/orders the user has interacted with"""
        from django.shortcuts import render
        from django.core.paginator import Paginator
        from .models import UserProduct, Record
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            
            # Get all UserProduct entries for this user (which links to records)
            user_products = UserProduct.objects.filter(user=user).select_related('record').order_by('-created_at')
            
            # Determine limit based on available_daily_order or level's orders_received_count
            limit = None
            if user.available_daily_order and user.available_daily_order > 0:
                limit = user.available_daily_order
            elif user.level and user.level.orders_received_count and user.level.orders_received_count > 0:
                limit = user.level.orders_received_count
            
            # Extract records from user_products
            records = []
            seen_record_ids = set()  # To avoid duplicates
            
            for user_product in user_products:
                if user_product.record and user_product.record.id not in seen_record_ids:
                    seen_record_ids.add(user_product.record.id)
                    records.append({
                        'id': user_product.record.id,
                        'product_name': user_product.record.title,
                        'price': user_product.record.price,
                        'ticket': user_product.record.id,  # Using record ID as ticket
                        'status': user_product.record.get_status_display(),
                        'status_value': user_product.record.status,
                        'created_at': user_product.record.created_at,
                        'user_product_id': user_product.id,
                    })
                    
                    # Apply limit if specified
                    if limit and len(records) >= limit:
                        break
            
            # Pagination
            paginator = Paginator(records, 25)  # Show 25 records per page
            page_number = request.GET.get('page', 1)
            try:
                page_obj = paginator.get_page(page_number)
            except:
                page_obj = paginator.get_page(1)
            
            context = {
                'user': user,
                'records': page_obj,
                'total_records': len(records),
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request, user),
            }
            
            return render(request, 'admin/referral_system/dealing_history.html', context)
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
        except Exception as e:
            messages.error(request, f'Error loading dealing history: {str(e)}')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))
    
    def more_actions_view(self, request, user_id):
        """Handle More Actions"""
        try:
            user = CustomUser.objects.get(pk=user_id)
            # Here you can implement additional actions or show a menu
            messages.info(request, f'More Actions for user: {user.username}')
            return HttpResponseRedirect(
                reverse('admin:referral_system_customuser_change', args=[user_id])
            )
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
            return HttpResponseRedirect(reverse('admin:referral_system_customuser_changelist'))


@admin.register(ReferralTracking)
class ReferralTrackingAdmin(admin.ModelAdmin):
    list_display = ['id', 'referrer', 'referred_user', 'agent', 'created_at']
    list_filter = ['agent', 'created_at']
    search_fields = ['referrer__username', 'referred_user__username', 'agent__username']
    readonly_fields = ['referrer', 'referred_user', 'agent', 'created_at']
    ordering = ['-created_at']


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'level', 'price', 'commission_percentage', 'commission', 'total_value', 'status', 'created_by', 'created_at', 'completed_at']
    list_filter = ['level', 'status', 'created_at', 'completed_at']
    search_fields = ['title', 'description', 'level__name', 'created_by__username']
    readonly_fields = ['id', 'commission_percentage', 'commission', 'total_value', 'created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    autocomplete_fields = ['level', 'created_by']
    filter_horizontal = ['reviews']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'level', 'created_by', 'image', 'reviews', 'status')
        }),
        ('Financial Details', {
            'fields': ('price', 'commission_percentage', 'commission', 'total_value'),
            'description': 'Commission percentage is automatically set from the selected level. Commission is calculated from price and commission percentage. Total value is price + commission.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'review_text_short', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['review_text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def review_text_short(self, obj):
        return obj.review_text[:50] + '...' if len(obj.review_text) > 50 else obj.review_text
    review_text_short.short_description = 'Review'


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = [
        'id',
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


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'is_default',
        'commission_rate',
        'minimum_balance',
        'orders_received_count',
        'withdrawals_count',
        'min_withdraw_amount',
        'max_withdraw_amount',
    ]
    list_filter = ['is_default', 'name']
    search_fields = ['name']
    ordering = ['id']


@admin.register(LevelUpgrade)
class LevelUpgradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'from_level', 'to_level', 'amount_paid', 'payment_method', 'upgraded_at']
    list_filter = ['payment_method', 'upgraded_at']
    search_fields = ['user__username', 'from_level__name', 'to_level__name', 'transaction_id']
    readonly_fields = ['upgraded_at']
    ordering = ['-upgraded_at']


@admin.register(LevelAssignment)
class LevelAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'assigned_by', 'from_level', 'to_level', 'assigned_at']
    list_filter = ['assigned_at', 'assigned_by__user_type']
    search_fields = ['user__username', 'assigned_by__username', 'from_level__name', 'to_level__name']
    readonly_fields = ['assigned_at']
    ordering = ['-assigned_at']

    
@admin.register(UserProduct)
class UserProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'record', 'position', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'record__title']
    ordering = ['user', 'position', 'created_at']
    autocomplete_fields = ['user', 'record']

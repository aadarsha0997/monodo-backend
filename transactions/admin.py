from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'transaction_type',
        'amount',
        'status',
        'account_holder_name',
        'bank_name',
        'processed_by',
        'created_at',
        'processed_at',
    ]
    list_filter = [
        'transaction_type',
        'status',
        'created_at',
        'processed_at',
    ]
    search_fields = [
        'user__username',
        'account_holder_name',
        'bank_name',
        'account_number',
    ]
    readonly_fields = [
        'id',
        'user',
        'transaction_type',
        'amount',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('id', 'user', 'transaction_type', 'amount', 'status')
        }),
        ('Bank Account Details', {
            'fields': (
                'account_number',
                'account_holder_name',
                'bank_name',
                'routing_number',
                'account_type',
            ),
            'classes': ('collapse',),
        }),
        ('Processing Information', {
            'fields': (
                'processed_by',
                'processed_at',
                'notes',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'processed_by')
    
    def save_model(self, request, obj, form, change):
        """Auto-set processed_by and processed_at when status changes"""
        if change and 'status' in form.changed_data:
            if obj.status in ['APPROVED', 'COMPLETED', 'REJECTED'] and not obj.processed_by:
                obj.processed_by = request.user
            if obj.status == 'COMPLETED' and not obj.processed_at:
                from django.utils import timezone
                obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['approve_transactions', 'reject_transactions', 'complete_transactions']
    
    def approve_transactions(self, request, queryset):
        """Approve selected transactions and deduct balance for withdrawals"""
        from django.utils import timezone
        from django.db import transaction as db_transaction
        from decimal import Decimal
        
        count = 0
        with db_transaction.atomic():
            for transaction in queryset.filter(status='PENDING'):
                user = transaction.user
                
                if transaction.transaction_type == 'DEPOSIT':
                    # For deposits, add balance when approved
                    user.balance += transaction.amount
                    user.save(update_fields=['balance'])
                    
                elif transaction.transaction_type == 'WITHDRAW':
                    # For withdrawals, deduct balance when approved
                    if user.balance >= transaction.amount:
                        user.balance -= transaction.amount
                        user.save(update_fields=['balance'])
                    else:
                        self.message_user(
                            request,
                            f'Warning: User {user.username} has insufficient balance for transaction {transaction.id}. Skipping.',
                            level='warning'
                        )
                        continue
                
                transaction.status = 'APPROVED'
                transaction.processed_by = request.user
                transaction.processed_at = timezone.now()
                transaction.save()
                count += 1
        
        self.message_user(request, f'{count} transaction(s) approved.')
    approve_transactions.short_description = "Approve selected transactions"
    
    def reject_transactions(self, request, queryset):
        """Reject selected transactions and refund user balance if already approved"""
        from django.utils import timezone
        from django.db import transaction as db_transaction
        
        count = 0
        with db_transaction.atomic():
            for transaction in queryset.filter(status__in=['PENDING', 'APPROVED']):
                # Only refund if it was already approved (balance was deducted)
                if transaction.transaction_type == 'WITHDRAW' and transaction.status == 'APPROVED':
                    # Refund the withdrawal amount
                    user = transaction.user
                    user.balance += transaction.amount
                    user.save(update_fields=['balance'])
                
                transaction.status = 'REJECTED'
                transaction.processed_by = request.user
                transaction.processed_at = timezone.now()
                transaction.save()
                count += 1
        
        self.message_user(request, f'{count} transaction(s) rejected. Refunded if previously approved.')
    reject_transactions.short_description = "Reject selected transactions"
    
    def complete_transactions(self, request, queryset):
        """Complete selected approved transactions"""
        from django.utils import timezone
        count = 0
        for transaction in queryset.filter(status='APPROVED'):
            transaction.status = 'COMPLETED'
            if not transaction.processed_at:
                transaction.processed_at = timezone.now()
            if not transaction.processed_by:
                transaction.processed_by = request.user
            transaction.save()
            count += 1
        self.message_user(request, f'{count} transaction(s) completed.')
    complete_transactions.short_description = "Complete selected approved transactions"

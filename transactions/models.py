from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from referral_system.models import CustomUser


class Transaction(models.Model):
    """Track deposits and withdrawals"""
    TRANSACTION_TYPE_CHOICES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # For withdrawals - bank account details
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    routing_number = models.CharField(max_length=50, blank=True, null=True)
    account_type = models.CharField(
        max_length=20,
        choices=[('checking', 'Checking'), ('savings', 'Savings')],
        blank=True,
        null=True
    )
    
    # Transaction metadata
    notes = models.TextField(blank=True, null=True, help_text="Admin notes or user notes")
    processed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_transactions',
        help_text="Admin/Agent who processed this transaction"
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} - ${self.amount} - {self.get_status_display()}"
    
    def clean(self):
        """Validate transaction data"""
        if self.transaction_type == 'WITHDRAW':
            if not self.account_number or not self.account_holder_name or not self.bank_name:
                raise ValidationError("Bank account details are required for withdrawals")
        
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

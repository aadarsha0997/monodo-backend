from rest_framework import serializers
from decimal import Decimal
from .models import Transaction
from referral_system.models import CustomUser, Level


class TransactionSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'user_username',
            'transaction_type',
            'amount',
            'status',
            'account_number',
            'account_holder_name',
            'bank_name',
            'routing_number',
            'account_type',
            'notes',
            'processed_by',
            'processed_by_username',
            'processed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'processed_by',
            'processed_at',
            'created_at',
            'updated_at',
        ]


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Deposit amount (must be greater than 0)"
    )
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes for this deposit")
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Deposit amount must be greater than zero")
        return value


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Withdrawal amount (must be greater than 0)"
    )
    withdraw_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Withdrawal password for verification"
    )
    account_number = serializers.CharField(required=True, max_length=50)
    account_holder_name = serializers.CharField(required=True, max_length=255)
    bank_name = serializers.CharField(required=True, max_length=255)
    routing_number = serializers.CharField(required=False, max_length=50, allow_blank=True)
    account_type = serializers.ChoiceField(
        choices=[('checking', 'Checking'), ('savings', 'Savings')],
        required=False,
        default='checking'
    )
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes for this withdrawal")
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be greater than zero")
        return value
    
    def validate_withdraw_password(self, value):
        """Validate withdrawal password"""
        return value


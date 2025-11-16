from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from .models import Transaction
from .serializers import TransactionSerializer, DepositSerializer, WithdrawSerializer
from referral_system.models import CustomUser, Level


class DepositView(APIView):
    """
    API endpoint for user deposits
    POST /api/transactions/deposit/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = Decimal(str(serializer.validated_data['amount']))
        notes = serializer.validated_data.get('notes', '')
        
        user = request.user
        
        try:
            with db_transaction.atomic():
                # Create deposit transaction (pending approval)
                deposit = Transaction.objects.create(
                    user=user,
                    transaction_type='DEPOSIT',
                    amount=amount,
                    status='PENDING',  # Requires admin approval
                    notes=notes
                )
                
                response_serializer = TransactionSerializer(deposit)
                return Response({
                    'message': 'Deposit request submitted successfully. It will be processed by admin.',
                    'transaction': response_serializer.data,
                    'current_balance': str(user.balance)
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Failed to process deposit: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawView(APIView):
    """
    API endpoint for user withdrawals
    POST /api/transactions/withdraw/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = Decimal(str(serializer.validated_data['amount']))
        withdraw_password = serializer.validated_data['withdraw_password']
        account_number = serializer.validated_data['account_number']
        account_holder_name = serializer.validated_data['account_holder_name']
        bank_name = serializer.validated_data['bank_name']
        routing_number = serializer.validated_data.get('routing_number', '')
        account_type = serializer.validated_data.get('account_type', 'checking')
        notes = serializer.validated_data.get('notes', '')
        
        user = request.user
        
        # Verify withdrawal password
        if user.withdraw_password != withdraw_password:
            return Response(
                {'error': 'Invalid withdrawal password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check user balance
        if user.balance < amount:
            return Response(
                {'error': 'Insufficient balance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user level for withdrawal limits
        level = user.level
        if not level:
            level = Level.get_default_level()
        
        # Validate withdrawal amount against level limits
        min_withdraw = level.min_withdraw_amount if level else Decimal('0.00')
        max_withdraw = level.max_withdraw_amount if level else Decimal('0.00')
        
        if min_withdraw > 0 and amount < min_withdraw:
            return Response(
                {'error': f'Minimum withdrawal amount is ${min_withdraw}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if max_withdraw > 0 and amount > max_withdraw:
            return Response(
                {'error': f'Maximum withdrawal amount is ${max_withdraw}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check pending withdrawals to ensure sufficient balance
            pending_withdrawals = Transaction.objects.filter(
                user=user,
                transaction_type='WITHDRAW',
                status__in=['PENDING', 'APPROVED']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            available_balance = user.balance - pending_withdrawals
            if available_balance < amount:
                return Response(
                    {'error': f'Insufficient balance. Available: ${available_balance}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with db_transaction.atomic():
                # Create withdrawal transaction (pending approval)
                withdrawal = Transaction.objects.create(
                    user=user,
                    transaction_type='WITHDRAW',
                    amount=amount,
                    status='PENDING',  # Requires admin approval
                    account_number=account_number,
                    account_holder_name=account_holder_name,
                    bank_name=bank_name,
                    routing_number=routing_number,
                    account_type=account_type,
                    notes=notes
                )
                
                response_serializer = TransactionSerializer(withdrawal)
                return Response({
                    'message': 'Withdrawal request submitted successfully. It will be processed by admin.',
                    'transaction': response_serializer.data,
                    'current_balance': str(user.balance),
                    'pending_withdrawals': str(pending_withdrawals + amount)
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Failed to process withdrawal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionListView(APIView):
    """
    API endpoint to list user's transactions
    GET /api/transactions/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        transaction_type = request.query_params.get('type', None)
        
        transactions = Transaction.objects.filter(user=user)
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type.upper())
        
        transactions = transactions.order_by('-created_at')[:50]  # Limit to recent 50
        
        serializer = TransactionSerializer(transactions, many=True)
        return Response({
            'count': transactions.count(),
            'transactions': serializer.data
        }, status=status.HTTP_200_OK)


class TransactionDetailView(APIView):
    """
    API endpoint to get transaction details
    GET /api/transactions/<transaction_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

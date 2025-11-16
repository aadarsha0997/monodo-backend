from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count, Q, Prefetch, Case, When, IntegerField, Value
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from decimal import Decimal
from .models import CustomUser, ReferralTracking, Record, LoginActivity, Level, Review
from   .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    AgentCreationSerializer,
    ReferralTrackingSerializer,
    UserRecordSerializer
)

def get_client_ip(request):
    """Retrieve the client IP address from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        if ip:
            return ip
    return request.META.get('REMOTE_ADDR')


def parse_user_agent(user_agent):
    """Crude user-agent parsing to extract browser, OS and device type."""
    if not user_agent:
        return 'Unknown', 'Unknown', 'unknown'

    ua = user_agent.lower()

    browser = 'Unknown'
    if 'chrome' in ua and 'edge' not in ua:
        browser = 'Chrome'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'edge' in ua:
        browser = 'Edge'
    elif 'msie' in ua or 'trident' in ua:
        browser = 'Internet Explorer'
    elif 'opera' in ua or 'opr' in ua:
        browser = 'Opera'

    os_name = 'Unknown'
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os x' in ua or 'macintosh' in ua:
        os_name = 'macOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        os_name = 'iOS'
    elif 'linux' in ua:
        os_name = 'Linux'

    device_type = 'desktop'
    mobile_keywords = ['iphone', 'android', 'mobile', 'blackberry', 'phone']
    tablet_keywords = ['ipad', 'tablet', 'nexus 7', 'nexus 10']

    if any(keyword in ua for keyword in tablet_keywords):
        device_type = 'tablet'
    elif any(keyword in ua for keyword in mobile_keywords):
        device_type = 'mobile'
    elif 'bot' in ua or 'crawl' in ua or 'spider' in ua:
        device_type = 'bot'

    return browser or 'Unknown', os_name or 'Unknown', device_type


def record_login_activity(request, user):
    """Persist login activity metadata for auditing."""
    try:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        browser, os_name, device_type = parse_user_agent(user_agent)
        ip_address = get_client_ip(request)

        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
        referrer = request.META.get('HTTP_REFERER')

        device_time_str = request.headers.get('X-Device-Time') or request.META.get('HTTP_X_DEVICE_TIME')
        device_time = parse_datetime(device_time_str) if device_time_str else None
        if device_time and device_time.tzinfo is None:
            device_time = timezone.make_aware(device_time, timezone.get_current_timezone())

        location = request.headers.get('X-Device-Location') or request.META.get('HTTP_X_DEVICE_LOCATION') or 'Unknown'

        extra_metadata = {
            'forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR'),
            'real_ip': request.META.get('HTTP_X_REAL_IP'),
            'host': request.get_host(),
            'request_path': request.path,
            'http_accept': request.META.get('HTTP_ACCEPT'),
            'content_type': request.META.get('CONTENT_TYPE'),
        }

        session_key = getattr(request.session, 'session_key', None)

        LoginActivity.objects.create(
            user=user,
            ip_address=ip_address,
            location=location,
            user_agent=user_agent,
            browser=browser or 'Unknown',
            operating_system=os_name or 'Unknown',
            device_type=device_type or 'unknown',
            accept_language=accept_language,
            session_key=session_key,
            referrer=referrer,
            device_time=device_time,
            extra_metadata=extra_metadata
        )
    except Exception as exc:
        # Avoid breaking login flow if logging fails
        print(f"Failed to record login activity for {user.username}: {exc}")


class UserRegistrationView(APIView):
    """
    API endpoint for user registration
    POST /api/register/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Registration successful',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    API endpoint for user login
    POST /api/login/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Record login activity
            record_login_activity(request, user)
            
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API endpoint to get current user profile
    GET /api/profile/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AgentCreationView(APIView):
    """
    API endpoint for SuperAdmin to create agents
    POST /api/agents/create/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is SuperAdmin
        if request.user.user_type != 'SUPERADMIN':
            return Response(
                {'error': 'Only SuperAdmin can create agents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AgentCreationSerializer(data=request.data)
        if serializer.is_valid():
            agent = serializer.save()
            return Response({
                'message': 'Agent created successfully',
                'agent': UserSerializer(agent).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentListView(generics.ListAPIView):
    """
    API endpoint to list all agents
    GET /api/agents/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        # Only SuperAdmin can view all agents
        if self.request.user.user_type == 'SUPERADMIN':
            return CustomUser.objects.filter(user_type='AGENT')
        return CustomUser.objects.none()


class AgentDetailView(APIView):
    """
    API endpoint to get agent details with statistics
    GET /api/agents/<agent_id>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        # Only SuperAdmin can view agent details
        if request.user.user_type != 'SUPERADMIN':
            return Response(
                {'error': 'Only SuperAdmin can view agent details'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            agent = CustomUser.objects.get(id=agent_id, user_type='AGENT')
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get statistics
        direct_referrals = agent.referrals.count()
        total_users_under_agent = agent.agent_users.count()
        
        data = UserSerializer(agent).data
        data['statistics'] = {
            'direct_referrals': direct_referrals,
            'total_users': total_users_under_agent,
        }
        
        return Response(data, status=status.HTTP_200_OK)


class MyReferralsView(APIView):
    """
    API endpoint to get current user's referrals
    GET /api/my-referrals/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        referrals = request.user.referrals.all()
        serializer = UserSerializer(referrals, many=True)
        
        return Response({
            'total_referrals': referrals.count(),
            'referrals': serializer.data
        }, status=status.HTTP_200_OK)


class ReferralTrackingListView(APIView):
    """
    API endpoint to view referral tracking
    GET /api/referral-tracking/
    For Agents: Shows all referrals under them
    For SuperAdmin: Shows all referrals with optional agent filter
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.user_type == 'SUPERADMIN':
            # SuperAdmin can see all or filter by agent
            agent_id = request.query_params.get('agent_id')
            if agent_id:
                trackings = ReferralTracking.objects.filter(agent_id=agent_id)
            else:
                trackings = ReferralTracking.objects.all()
        
        elif user.user_type == 'AGENT':
            # Agent can only see their referrals
            trackings = ReferralTracking.objects.filter(agent=user)
        
        else:
            # Normal users can see their own referrals
            trackings = ReferralTracking.objects.filter(referrer=user)
        
        serializer = ReferralTrackingSerializer(trackings, many=True)
        
        return Response({
            'total_records': trackings.count(),
            'referral_tracking': serializer.data
        }, status=status.HTTP_200_OK)


class DashboardStatsView(APIView):
    """
    API endpoint for dashboard statistics
    GET /api/dashboard/stats/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.user_type == 'SUPERADMIN':
            stats = {
                'total_agents': CustomUser.objects.filter(user_type='AGENT').count(),
                'total_users': CustomUser.objects.filter(user_type='USER').count(),
                'total_referrals': ReferralTracking.objects.count(),
            }
        
        elif user.user_type == 'AGENT':
            stats = {
                'direct_referrals': user.referrals.count(),
                'total_users_under_me': user.agent_users.count(),
                'my_referral_code': user.referral_code,
            }
        
        else:  # Normal User
            stats = {
                'my_referrals': user.referrals.count(),
                'my_referral_code': user.referral_code,
                'referred_by': user.referred_by.username if user.referred_by else None,
                'my_agent': user.agent.username if user.agent else None,
            }
        
        return Response(stats, status=status.HTTP_200_OK)


class ValidateReferralCodeView(APIView):
    """
    API endpoint to validate referral code
    POST /api/validate-referral-code/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        referral_code = request.data.get('referral_code', '').strip()
        
        if not referral_code:
            return Response(
                {'valid': False, 'message': 'Referral code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(referral_code=referral_code)
            return Response({
                'valid': True,
                'referrer': {
                    'username': user.username,
                    'user_type': user.get_user_type_display()
                }
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {'valid': False, 'message': 'Invalid referral code'},
                status=status.HTTP_404_NOT_FOUND
            )
class UserRecordImagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        level = request.user.level

        if not level:
            agent = getattr(request.user, 'agent', None)
            if agent and agent.level:
                level = agent.level
            else:
                level = Level.get_default_level()

        if not level:
            return Response(
                {
                    'total_records': 0,
                    'user_level': None,
                    'records': []
                },
                status=status.HTTP_200_OK
            )

        # Check if there's a status filter in query parameters
        status_filter = request.GET.get('status', '').upper()
        filter_by_status = status_filter in ['PENDING', 'COMPLETED', 'CANCELLED']
        
        # Build base queryset
        status_list = ['PENDING', 'COMPLETED']
        if filter_by_status:
            status_list = [status_filter]
        
        records = Record.objects.filter(
            level=level,
            status__in=status_list
        ).select_related(
            'level',
            'created_by'
        ).prefetch_related(
            Prefetch(
                'reviews',
                queryset=Review.objects.filter(is_active=True).order_by('-created_at'),
                to_attr='active_reviews'
            )
        ).annotate(
            status_order=Case(
                When(status='PENDING', then=Value(0)),
                When(status='COMPLETED', then=Value(1)),
                default=Value(2),
                output_field=IntegerField()
            )
        ).order_by('status_order', 'title')

        # Get user and refresh from database to get latest data
        user = request.user
        user.refresh_from_db()
        user_balance = user.balance or Decimal('0.00')
        
        # If filtering by status, show all records matching that status
        if filter_by_status:
            if status_filter == 'PENDING':
                # When filtering by PENDING, show all pending records (user can submit any of them)
                records_list = list(records)
            elif status_filter == 'COMPLETED':
                # When filtering by COMPLETED, show all completed records
                records_list = list(records)
            else:
                records_list = list(records)
        else:
            # Default behavior: Filter to show:
            # 1. All completed records
            # 2. The first pending record with insufficient balance (if any)
            # 3. If no insufficient balance records, the first pending record with sufficient balance
            
            pending_records = [r for r in records if r.status == 'PENDING']
            completed_records = [r for r in records if r.status == 'COMPLETED']
            insufficient_balance_records = []
            sufficient_balance_records = []
            
            for record in pending_records:
                record_price = record.price or Decimal('0.00')
                if user_balance < record_price:
                    # Balance is insufficient for this record
                    insufficient_balance_records.append(record)
                else:
                    # Balance is sufficient for this record
                    sufficient_balance_records.append(record)
            
            # Build records list: completed records + one pending record
            records_list = completed_records.copy()  # Include all completed records
            
            # Add the appropriate pending record
            if insufficient_balance_records:
                # Show only the first pending record with insufficient balance
                records_list.append(insufficient_balance_records[0])
            elif sufficient_balance_records:
                # Show only the first pending record with sufficient balance
                records_list.append(sufficient_balance_records[0])
            # If no pending records, only completed records are shown

        serializer = UserRecordSerializer(
            records_list,
            many=True,
            context={'request': request}
        )

        # Count completed records for completion message
        # Get all records (not just shown ones) to count completed
        all_records = list(records)
        completed_count = sum(1 for r in all_records if r.status == 'COMPLETED')
        
        # Count total pending records for context
        total_pending = len(pending_records)
        total_insufficient = len(insufficient_balance_records)
        
        all_completed = False
        completion_message = None
        
        # Limit based on available_daily_order or level's orders_received_count
        limit = None
        if user.available_daily_order and user.available_daily_order > 0:
            limit = user.available_daily_order
        elif level.orders_received_count and level.orders_received_count > 0:
            limit = level.orders_received_count
        
        if limit and limit > 0:
            if completed_count >= limit:
                all_completed = True
                level_name = level.get_name_display() if level else "your level"
                completion_message = f"Congratulations! You have completed all {limit} orders for the {level_name} level."
            else:
                remaining = limit - completed_count
                completion_message = f"You have {remaining} order(s) remaining out of {limit} for the {level.get_name_display() if level else 'your'} level."

        user_level = {
            'id': str(level.id),
            'name': level.name,
            'display_name': level.get_name_display(),
            'commission_rate': str(level.commission_rate),
            'minimum_balance': str(level.minimum_balance),
            'orders_received_count': level.orders_received_count,
        }
        
        return Response({
            'total_records': len(serializer.data),  # Use actual returned count
            'user_level': user_level,
            'records': serializer.data,
            'user_balance': str(user.balance or Decimal('0.00')),
            'todays_commission': str(user.todays_commission or Decimal('0.00')),
            'available_daily_order': user.available_daily_order,
            'completed_count': completed_count,
            'all_completed': all_completed,
            'completion_message': completion_message,
            'limit': limit,
            'frozen_amount': str(user.frozen_amount or Decimal('0.00')),
        }, status=status.HTTP_200_OK)


class RecordSubmitReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        record_id = request.data.get('record_id')
        review_id = request.data.get('review_id')

        if not record_id or not review_id:
            return Response({'detail': 'record_id and review_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            record = Record.objects.select_related('level').prefetch_related('reviews').get(id=record_id)
        except Record.DoesNotExist:
            return Response({'detail': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if record.status == 'COMPLETED':
            return Response({'detail': 'Record has already been completed.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            record.reviews.get(id=review_id, is_active=True)
        except Review.DoesNotExist:
            return Response({'detail': 'Review not associated with this record.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user has sufficient balance before allowing submission
        user = request.user
        user.refresh_from_db()  # Get latest balance
        user_balance = user.balance or Decimal('0.00')
        record_price = record.price or Decimal('0.00')
        
        # Calculate insufficient amount if balance is less than price
        if user_balance < record_price:
            insufficient_amount = record_price - user_balance
            
            # Update frozen amount with the insufficient amount
            from django.db import transaction
            with transaction.atomic():
                user = CustomUser.objects.select_for_update().get(pk=user.pk)
                current_frozen = user.frozen_amount or Decimal('0.00')
                # Set frozen amount to insufficient amount (replace, not accumulate)
                user.frozen_amount = insufficient_amount
                user.save(update_fields=['frozen_amount'])
                user.refresh_from_db()
            
            return Response({
                'detail': f'Balance not sufficient. You need ${record_price:.2f} but you have ${user_balance:.2f}. Please deposit ${insufficient_amount:.2f} to proceed.',
                'error': 'insufficient_balance',
                'required_amount': str(record_price),
                'current_balance': str(user_balance),
                'insufficient_amount': str(insufficient_amount),
                'frozen_amount': str(user.frozen_amount)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Balance is sufficient, proceed with submission
        record.status = 'COMPLETED'
        record.completed_at = timezone.now()
        record.save()

        user.taking_orders_today = (user.taking_orders_today or 0) + 1
        user.orders_received_today = (user.orders_received_today or 0) + 1
        
        # Add commission to user balance and todays_commission when task is completed
        if record.commission:
            commission_amount = record.commission
            user.balance = (user.balance or Decimal('0.00')) + commission_amount
            user.todays_commission = (user.todays_commission or Decimal('0.00')) + commission_amount
        
        # Reset frozen_amount to 0 when balance becomes sufficient and user submits
        user.frozen_amount = Decimal('0.00')
        
        user.save(update_fields=['taking_orders_today', 'orders_received_today', 'balance', 'todays_commission', 'frozen_amount'])

        serializer = UserRecordSerializer(record, context={'request': request})
        return Response({
            'record': serializer.data,
            'user_stats': {
                'orders_received_today': user.orders_received_today,
                'taking_orders_today': user.taking_orders_today,
                'balance': str(user.balance),
                'todays_commission': str(user.todays_commission),
                'frozen_amount': str(user.frozen_amount)
            }
        }, status=status.HTTP_200_OK)


class SaveBankAccountView(APIView):
    """
    API endpoint to save/update user's bank account details
    POST /api/bank-account/save/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        
        account_number = request.data.get('account_number', '').strip()
        account_holder_name = request.data.get('account_holder_name', '').strip()
        bank_name = request.data.get('bank_name', '').strip()
        routing_number = request.data.get('routing_number', '').strip()
        account_type = request.data.get('account_type', 'checking')

        # Validation
        if not account_number:
            return Response({'error': 'Account number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not account_holder_name:
            return Response({'error': 'Account holder name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not bank_name:
            return Response({'error': 'Bank name is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Save bank account details
        user.bank_account_number = account_number
        user.bank_account_holder_name = account_holder_name
        user.bank_name = bank_name
        user.bank_routing_number = routing_number or None
        user.bank_account_type = account_type
        user.save(update_fields=[
            'bank_account_number',
            'bank_account_holder_name',
            'bank_name',
            'bank_routing_number',
            'bank_account_type'
        ])

        serializer = UserSerializer(user)
        return Response({
            'message': 'Bank account details saved successfully',
            'bank_account': serializer.data.get('bank_account')
        }, status=status.HTTP_200_OK)
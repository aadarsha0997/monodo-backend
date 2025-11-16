from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count, Q, Prefetch, Case, When, IntegerField, Value
from django.utils import timezone
from django.utils.dateparse import parse_datetime
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

        records = Record.objects.filter(
            level=level,
            status__in=['PENDING', 'COMPLETED']
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

        serializer = UserRecordSerializer(
            records,
            many=True,
            context={'request': request}
        )

        user_level = {
            'id': str(level.id),
            'name': level.name,
            'display_name': level.display_name,
            'image_upload_limit': level.image_upload_limit,
            'commission_rate': str(level.commission_rate),
            'minimum_balance': str(level.minimum_balance),
        }

        return Response({
            'total_records': records.count(),
            'user_level': user_level,
            'records': serializer.data,
            'user_balance': str(request.user.balance),
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

        record.status = 'COMPLETED'
        record.completed_at = timezone.now()
        record.save()

        user = request.user
        user.taking_orders_today = (user.taking_orders_today or 0) + 1
        user.save(update_fields=['taking_orders_today'])

        serializer = UserRecordSerializer(record, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
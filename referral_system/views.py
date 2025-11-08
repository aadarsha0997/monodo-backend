from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count, Q
from .models import CustomUser, ReferralTracking
from   .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    AgentCreationSerializer,
    ReferralTrackingSerializer
)


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
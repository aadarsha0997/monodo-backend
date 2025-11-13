from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, ReferralTracking, Record, Review


class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_withdraw_password = serializers.CharField(write_only=True, required=True)
    login_password = serializers.CharField(write_only=True, required=True, min_length=6)
    confirm_login_password = serializers.CharField(write_only=True, required=True)
    invitation_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'phone_number',
            'withdraw_password',
            'confirm_withdraw_password',
            'login_password',
            'confirm_login_password',
            'invitation_code'
        ]
        extra_kwargs = {
            'withdraw_password': {'write_only': True},
        }

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def validate(self, data):
        # Validate login password confirmation
        if data['login_password'] != data['confirm_login_password']:
            raise serializers.ValidationError({
                "confirm_login_password": "Login passwords do not match"
            })
        
        # Validate withdraw password confirmation
        if data['withdraw_password'] != data['confirm_withdraw_password']:
            raise serializers.ValidationError({
                "confirm_withdraw_password": "Withdraw passwords do not match"
            })
        
        # Validate invitation code if provided
        invitation_code = data.get('invitation_code', '').strip()
        if invitation_code:
            try:
                referrer = CustomUser.objects.get(referral_code=invitation_code)
                data['referrer'] = referrer
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({
                    "invitation_code": "Invalid invitation code"
                })
        else:
            data['referrer'] = None
        
        return data

    def create(self, validated_data):
        # Remove confirmation fields
        validated_data.pop('confirm_withdraw_password')
        validated_data.pop('confirm_login_password')
        
        # Extract login password and invitation code
        login_password = validated_data.pop('login_password')
        validated_data.pop('invitation_code', None)
        referrer = validated_data.pop('referrer', None)
        
        # Create user with updated parameters
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            phone_number=validated_data['phone_number'],
            login_password=login_password,
            withdraw_password=validated_data['withdraw_password'],
            user_type='USER',
            referred_by=referrer
        )
        
        # Create referral tracking
        if referrer:
            ReferralTracking.objects.create(
                referrer=referrer,
                referred_user=user
            )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    login_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('login_password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            data['user'] = user
        else:
            raise serializers.ValidationError("Must include username and password")

        return data


class UserSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    referred_by_username = serializers.CharField(source='referred_by.username', read_only=True, allow_null=True)
    agent_username = serializers.CharField(source='agent.username', read_only=True, allow_null=True)
    total_referrals = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'phone_number',
            'user_type',
            'user_type_display',
            'level',
            'referral_code',
            'referred_by_username',
            'agent_username',
            'total_referrals',
            'taking_orders_today',
            'balance',
            'date_joined',
            'is_active'
        ]
        read_only_fields = ['id', 'referral_code', 'date_joined', 'taking_orders_today', 'balance']

    def get_total_referrals(self, obj):
        return obj.referrals.count()

    def get_level(self, obj):
        level = getattr(obj, 'level', None)
        if not level:
            return None
        return {
            'id': str(level.id),
            'name': level.name,
            'display_name': level.display_name,
            'commission_rate': str(level.commission_rate),
            'image_upload_limit': level.image_upload_limit,
        }



class AgentCreationSerializer(serializers.ModelSerializer):
    login_password = serializers.CharField(write_only=True, required=True, min_length=6)
    confirm_login_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'phone_number',
            'withdraw_password',
            'login_password',
            'confirm_login_password'
        ]

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def validate(self, data):
        if data['login_password'] != data['confirm_login_password']:
            raise serializers.ValidationError({
                "confirm_login_password": "Passwords do not match"
            })
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_login_password')
        login_password = validated_data.pop('login_password')
        
        agent = CustomUser.objects.create_user(
            username=validated_data['username'],
            phone_number=validated_data['phone_number'],
            login_password=login_password,
            withdraw_password=validated_data['withdraw_password'],
            user_type='AGENT'
        )
        return agent


class ReferralTrackingSerializer(serializers.ModelSerializer):
    referrer_username = serializers.CharField(source='referrer.username', read_only=True)
    referred_user_username = serializers.CharField(source='referred_user.username', read_only=True)
    agent_username = serializers.CharField(source='agent.username', read_only=True, allow_null=True)

    class Meta:
        model = ReferralTracking
        fields = [
            'id',
            'referrer_username',
            'referred_user_username',
            'agent_username',
            'created_at'
        ]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'review_text',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'review_text',
            'is_active',
            'created_at',
            'updated_at',
        ]


class UserRecordSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    created_by = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            'id',
            'title',
            'description',
            'price',
            'commission',
            'commission_percentage',
            'total_value',
            'status',
            'created_at',
            'updated_at',
            'completed_at',
            'level',
            'image_url',
            'created_by',
            'reviews',
        ]
        read_only_fields = fields

    def get_level(self, obj):
        level = getattr(obj, 'level', None)
        if not level:
            return None
        return {
            'id': str(level.id),
            'name': level.name,
            'display_name': level.display_name,
            'image_upload_limit': level.image_upload_limit,
            'commission_rate': str(level.commission_rate),
        }

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_reviews(self, obj):
        reviews = getattr(obj, 'active_reviews', None)
        if reviews is None:
            reviews = obj.reviews.filter(is_active=True).order_by('-created_at')
        return ReviewSerializer(reviews, many=True).data
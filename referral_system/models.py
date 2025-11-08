from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
import random
import string


class CustomUserManager(BaseUserManager):
    def create_user(self, username, phone_number, password=None, login_password=None, withdraw_password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        if not phone_number:
            raise ValueError('Phone number is required')
        
        actual_password = login_password or password
        if not actual_password:
            raise ValueError('Password is required')
        
        user = self.model(
            username=username,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(actual_password)
        user.withdraw_password = withdraw_password or actual_password
        
        # Set is_staff=True for agents
        if user.user_type == 'AGENT':
            user.is_staff = True
        
        user.save(using=self._db)
        return user

    def create_superuser(self, username, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'SUPERADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(
            username=username, 
            phone_number=phone_number, 
            password=password,
            withdraw_password=password,
            **extra_fields
        )


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('AGENT', 'Agent'),
        ('USER', 'Normal User'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    
    withdraw_password = models.CharField(max_length=128)
    
    # User type
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='USER')
    
    # Referral system
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='referrals'
    )
    
    # Agent relationship
    agent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_users',
        limit_choices_to={'user_type': 'AGENT'}
    )
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        # Set agent based on who referred them
        if self.referred_by and not self.agent:
            if self.referred_by.user_type == 'AGENT':
                self.agent = self.referred_by
            elif self.referred_by.user_type == 'USER' and self.referred_by.agent:
                self.agent = self.referred_by.agent
        
        # Set is_staff for agents
        if self.user_type == 'AGENT':
            self.is_staff = True
        elif self.user_type == 'USER':
            self.is_staff = False
        
        # Check if this is being converted to an agent
        is_new = self.pk is None
        was_agent = False
        if not is_new:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                was_agent = old_instance.user_type == 'AGENT'
            except CustomUser.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Add permissions for agents after saving
        if self.user_type == 'AGENT' and not self.is_superuser:
            if is_new or not was_agent:
                self.assign_agent_permissions()
    
    def assign_agent_permissions(self):
        """Assign ONLY necessary permissions for agents to view/manage their users"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        try:
            # Clear all existing permissions first
            self.user_permissions.clear()
            
            # Get permissions for CustomUser model - ONLY view, add, and change
            user_ct = ContentType.objects.get_for_model(CustomUser)
            user_permissions = Permission.objects.filter(
                content_type=user_ct,
                codename__in=['view_customuser', 'add_customuser', 'change_customuser']
            )
            
            # Add ONLY these 3 permissions
            if user_permissions:
                self.user_permissions.add(*user_permissions)
                
        except Exception as e:
            print(f"Could not assign permissions: {e}")

    @staticmethod
    def generate_referral_code(length=8):
        """Generate a unique referral code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not CustomUser.objects.filter(referral_code=code).exists():
                return code


class ReferralTracking(models.Model):
    """Track referral relationships and statistics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='referrer_tracking'
    )
    referred_user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='referred_tracking'
    )
    agent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='agent_tracking',
        limit_choices_to={'user_type': 'AGENT'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'referral_tracking'
        verbose_name = 'Referral Tracking'
        verbose_name_plural = 'Referral Trackings'
        unique_together = ['referrer', 'referred_user']

    def __str__(self):
        return f"{self.referrer.username} referred {self.referred_user.username}"

    def save(self, *args, **kwargs):
        # Automatically set agent
        if not self.agent:
            if self.referrer.user_type == 'AGENT':
                self.agent = self.referrer
            elif self.referrer.agent:
                self.agent = self.referrer.agent
        super().save(*args, **kwargs)
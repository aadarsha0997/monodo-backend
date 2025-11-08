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
            withdraw_password=password,  # Use same password for withdraw
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
    

    withdraw_password = models.CharField(max_length=128)  # Consider hashing this too
    
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
    
    # Agent relationship (for tracking which agent a user belongs to)
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
        
        super().save(*args, **kwargs)

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




class Record(models.Model):
    """Track bookings/tours with commission and status"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User who created/owns this record
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='records'
    )
    
    # Agent associated with this record
    agent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_records',
        limit_choices_to={'user_type': 'AGENT'}
    )
    
    # Tour/Booking details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.URLField(max_length=500, blank=True, null=True)
    
    # Financial details
    price = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Commission percentage (optional - for tracking)
    commission_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Commission percentage (e.g., 7.00 for 7%)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'records'
        verbose_name = 'Record'
        verbose_name_plural = 'Records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['agent', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username} - {self.status}"

    def save(self, *args, **kwargs):
        # Auto-assign agent from user
        if not self.agent and self.user.agent:
            self.agent = self.user.agent
        
        # Auto-calculate total value
        self.total_value = self.price + self.commission
        
        # Auto-calculate commission percentage if not set
        if self.commission and self.price and not self.commission_percentage:
            self.commission_percentage = (self.commission / self.price) * 100
        
        # Set completed_at timestamp when status changes to COMPLETED
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
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

        level = extra_fields.pop('level', None)
        
        user = self.model(
            username=username,
            phone_number=phone_number,
            level=level or Level.get_default_level(),
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


class Level(models.Model):
    """Membership levels/tiers with different benefits"""
    LEVEL_CHOICES = (
        ('BASIC', 'Basic'),
        ('GOLD', 'Gold'),
        ('DIAMOND', 'Diamond'),
        ('PLATINUM', 'Platinum'),
    )
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Mark this level as the default assigned to new members"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Commission percentage (e.g., 7.00 for 7%)"
    )
    minimum_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Minimum balance required to maintain this level"
    )
    orders_received_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of orders received while at this level"
    )
    withdrawals_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of withdrawals made while at this level"
    )
    min_withdraw_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Minimum amount a member can withdraw"
    )
    max_withdraw_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Maximum amount a member can withdraw at once (0 means no limit)"
    )
    
    DEFAULT_LEVEL_NAME = 'BASIC'

    class Meta:
        db_table = 'levels'
        verbose_name = 'Level'
        verbose_name_plural = 'Levels'
        ordering = ['id']
    
    def clean(self):
        super().clean()
        if (
            self.max_withdraw_amount
            and self.min_withdraw_amount
            and self.max_withdraw_amount > Decimal('0.00')
            and self.max_withdraw_amount < self.min_withdraw_amount
        ):
            raise ValidationError("Maximum withdrawal amount cannot be less than minimum withdrawal amount.")

    def __str__(self):
        return f"{self.get_name_display()} (Commission: {self.commission_rate}%)"

    @classmethod
    def get_default_level(cls):
        level = cls.objects.filter(is_default=True).order_by('id').first()
        if level:
            return level
        level = cls.objects.filter(name=cls.DEFAULT_LEVEL_NAME).order_by('id').first()
        if level:
            return level
        return cls.objects.order_by('id').first()

    @classmethod
    def get_default_level_id(cls):
        level = cls.get_default_level()
        return level.id if level else None


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('AGENT', 'Agent'),
        ('USER', 'Normal User'),
    )

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    
    withdraw_password = models.CharField(max_length=128)
    
    # User type
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='USER')
    
    # Level/Tier system
    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="User's membership level"
    )
    
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

    # Daily tracking
    taking_orders_today = models.PositiveIntegerField(default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('20.00'))
    
    # Additional user fields
    available_daily_order = models.PositiveIntegerField(
        default=0,
        help_text="Available orders for today"
    )
    todays_commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Commission earned today"
    )
    credibility = models.IntegerField(
        default=100,
        help_text="Credibility score (0-100)"
    )
    frozen_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount frozen/held"
    )
    allow_withdrawal = models.BooleanField(
        default=True,
        help_text="Whether user is allowed to withdraw"
    )
    rob_single = models.BooleanField(
        default=False,
        help_text="Rob Single status"
    )
    operate = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Operation details"
    )
    place = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Place/Location"
    )
    
    # Bank account details for withdrawals
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_routing_number = models.CharField(max_length=50, blank=True, null=True)
    bank_account_type = models.CharField(
        max_length=20,
        choices=[('checking', 'Checking'), ('savings', 'Savings')],
        blank=True,
        null=True
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

    def generate_referral_code(self):
        """Generate a unique referral code"""
        if self.referral_code:
            return  # Don't regenerate if code already exists
        
        length = 8
        max_attempts = 100
        
        for _ in range(max_attempts):
            # Generate code using uppercase letters and numbers
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            
            # Check if code is unique (exclude current user if updating)
            queryset = CustomUser.objects.filter(referral_code=code)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
            if not queryset.exists():
                self.referral_code = code
                return
        
        # Fallback: use user ID with random suffix if all attempts fail
        # This should rarely happen, but ensures we always have a code
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        # If no ID yet, use a random number
        if self.pk:
            self.referral_code = f"{self.pk}{random_suffix}"
        else:
            # For new users, this will be set after save
            pass

    def save(self, *args, **kwargs):
        # Set is_staff for agents
        if self.user_type == 'AGENT':
            self.is_staff = True
        elif self.user_type == 'USER':
            self.is_staff = False
        
        # Check if level is being set or changed
        level_changed = False
        is_new_user = not self.pk
        
        if self.pk:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                # Check if level has changed
                if old_instance.level != self.level:
                    level_changed = True
            except CustomUser.DoesNotExist:
                is_new_user = True
        
        # If level is selected, set available_daily_order from level's orders_received_count
        # This happens when creating a new user with a level, or when level is changed
        if self.level and (is_new_user or level_changed):
            # Set available_daily_order to level's orders_received_count
            self.available_daily_order = self.level.orders_received_count
        
        # Generate referral code if not set
        if not self.referral_code:
            self.generate_referral_code()
        
        # Save the user
        super().save(*args, **kwargs)
        
        # If referral code still not set (fallback scenario), regenerate after getting ID
        if not self.referral_code:
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.referral_code = f"{self.id}{random_suffix}"
            CustomUser.objects.filter(pk=self.pk).update(referral_code=self.referral_code)

    def __str__(self):
        level_name = self.level.get_name_display() if self.level else 'No Level'
        return f"{self.username} ({self.get_user_type_display()}) - {level_name}"



class ReferralTracking(models.Model):
    """Track referral relationships and statistics"""
    id = models.AutoField(primary_key=True)
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
        if not self.agent:
            if self.referrer.user_type == 'AGENT':
                self.agent = self.referrer
            elif self.referrer.agent:
                self.agent = self.referrer.agent
        super().save(*args, **kwargs)


class Record(models.Model):
    """Level-based record templates created by admins/agents."""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.AutoField(primary_key=True)

    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='records',
        default=Level.get_default_level_id,
        help_text="Level this record belongs to"
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_records',
        limit_choices_to={'user_type__in': ['SUPERADMIN', 'AGENT']},
        help_text="Admin or Agent who created this record"
    )

    # Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='record_images/', blank=True, null=True)
    reviews = models.ManyToManyField(
        'Review',
        blank=True,
        related_name='records',
        help_text="Selectable reviews shown with this record"
    )

    # Financial details
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Commission percentage (auto-calculated from level if not provided)"
    )
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

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
        ordering = ['level__id', 'title']
        indexes = [
            models.Index(fields=['level', 'status']),
        ]

    def save(self, *args, **kwargs):
        # Check if level is being set or changed
        level_changed = False
        is_new_record = not self.pk
        
        if self.pk:
            try:
                old_instance = Record.objects.get(pk=self.pk)
                # Check if level has changed
                if old_instance.level != self.level:
                    level_changed = True
            except Record.DoesNotExist:
                is_new_record = True
        
        # If level is selected, set commission_percentage from level's commission_rate
        # This happens when creating a new record with a level, or when level is changed
        if self.level and (is_new_record or level_changed or not self.commission_percentage):
            # Set commission_percentage to level's commission_rate
            self.commission_percentage = self.level.commission_rate
        
        # Calculate commission from price and commission_percentage
        # commission = price * commission_percentage (commission_percentage is already a decimal, e.g., 0.08 for 8%)
        if self.price and self.commission_percentage:
            commission_calc = self.price * self.commission_percentage
            # Round to 2 decimal places
            self.commission = commission_calc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.commission = Decimal('0.00')
        
        # Calculate total_value (price + commission)
        if self.price:
            self.total_value = (self.price + (self.commission or Decimal('0.00'))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        else:
            self.total_value = Decimal('0.00')
        
        # Save the record
        super().save(*args, **kwargs)

    def __str__(self):
        level_name = self.level.get_name_display() if self.level else 'No Level'
        return f"{self.title} ({level_name})"

    

class Review(models.Model):
    """Reusable review texts that can be attached to multiple records."""

    id = models.AutoField(primary_key=True)
    review_text = models.TextField(help_text="The review content that will be shown to users")
    is_active = models.BooleanField(default=True, help_text="Only active reviews will be included in APIs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.review_text[:50]}..." if len(self.review_text) > 50 else self.review_text


class LevelUpgrade(models.Model):
    """Track user level upgrades"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='level_upgrades'
    )
    from_level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='upgrades_from'
    )
    to_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='upgrades_to'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment tracking
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    upgraded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'level_upgrades'
        verbose_name = 'Level Upgrade'
        verbose_name_plural = 'Level Upgrades'
        ordering = ['-upgraded_at']
    
    def __str__(self):
        from_name = self.from_level.get_name_display() if self.from_level else 'None'
        return f"{self.user.username}: {from_name} → {self.to_level.get_name_display()}"


class LevelAssignment(models.Model):
    """Keep a history of level assignments performed by agents or super admins."""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='level_assignments'
    )
    assigned_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_levels',
        limit_choices_to={'user_type__in': ['SUPERADMIN', 'AGENT']}
    )
    from_level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment_from_level'
    )
    to_level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment_to_level'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'level_assignments'
        verbose_name = 'Level Assignment'
        verbose_name_plural = 'Level Assignments'
        ordering = ['-assigned_at']

    def __str__(self):
        from_level_name = self.from_level.get_name_display() if self.from_level else 'None'
        to_level_name = self.to_level.get_name_display() if self.to_level else 'None'
        assigned_by = self.assigned_by.username if self.assigned_by else 'Unknown'
        return f"{self.user.username}: {from_level_name} → {to_level_name} by {assigned_by}"


class LoginActivity(models.Model):
    """Track user login activity, including device and location information."""
    DEVICE_TYPES = (
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('bot', 'Bot'),
        ('unknown', 'Unknown'),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='login_activities'
    )
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, default='Unknown', help_text="City / Country if available")
    user_agent = models.TextField(blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, default='Unknown')
    operating_system = models.CharField(max_length=100, blank=True, default='Unknown')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='unknown')
    accept_language = models.CharField(max_length=255, blank=True, null=True)
    session_key = models.CharField(max_length=255, blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    device_time = models.DateTimeField(blank=True, null=True, help_text="Client-reported device time (if provided)")
    extra_metadata = models.JSONField(blank=True, null=True, help_text="Stores additional headers or info")

    class Meta:
        db_table = 'login_activity'
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['browser']),
            models.Index(fields=['operating_system']),
        ]

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time:%Y-%m-%d %H:%M:%S}"

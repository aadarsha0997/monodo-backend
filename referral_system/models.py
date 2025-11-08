from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    
    # Benefits
    image_upload_limit = models.IntegerField(
        default=10,
        help_text="Number of images user can upload per record"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        help_text="Commission percentage (e.g., 7.00 for 7%)"
    )
    
    # Pricing
    upgrade_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Price to upgrade to this level (0 for free/default level)"
    )
    
    # Additional features
    priority_support = models.BooleanField(default=False, help_text="Get priority customer support")
    featured_listing = models.BooleanField(default=False, help_text="Records appear as featured")
    max_records_per_month = models.IntegerField(default=100, help_text="Maximum records per month")
    
    # Level order (for upgrades)
    level_order = models.IntegerField(default=0, help_text="Higher number = higher tier (1=Basic, 2=Gold, etc)")
    
    # Icon/Badge for display
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for level badge/icon")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    DEFAULT_LEVEL_NAME = 'BASIC'

    class Meta:
        db_table = 'levels'
        verbose_name = 'Level'
        verbose_name_plural = 'Levels'
        ordering = ['level_order']
    
    def __str__(self):
        return f"{self.display_name} (Images: {self.image_upload_limit}, Commission: {self.commission_rate}%)"

    @classmethod
    def get_default_level(cls):
        level = (
            cls.objects.filter(name=cls.DEFAULT_LEVEL_NAME, is_active=True)
            .order_by('level_order')
            .first()
        )
        if level:
            return level
        return (
            cls.objects.filter(is_active=True)
            .order_by('level_order')
            .first()
        )

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        level_name = self.level.display_name if self.level else 'No Level'
        return f"{self.username} ({self.get_user_type_display()}) - {level_name}"

    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()

        # Ensure default level is set
        if not self.level:
            default_level = Level.get_default_level()
            if default_level:
                self.level = default_level
        
        # Set agent and inherit level from agent
        if self.referred_by and not self.agent:
            if self.referred_by.user_type == 'AGENT':
                self.agent = self.referred_by
                # Inherit level from agent if user doesn't have one
                if not self.level and self.agent.level:
                    self.level = self.agent.level
            elif self.referred_by.user_type == 'USER' and self.referred_by.agent:
                self.agent = self.referred_by.agent
                # Inherit level from agent if user doesn't have one
                if not self.level and self.agent.level:
                    self.level = self.agent.level
        
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

    def assign_level(self, level, assigned_by):
        """
        Assign a membership level to the user.

        Only SUPERADMIN or AGENT users can perform the assignment for normal users.
        """
        if assigned_by is None:
            raise ValidationError("Assigned by user is required for level assignment.")

        if assigned_by.user_type not in {'SUPERADMIN', 'AGENT'}:
            raise ValidationError("Only SuperAdmin or Agent users can assign levels.")

        if self.user_type != 'USER':
            raise ValidationError("Only normal users can receive level assignments through this method.")

        if level is not None and not level.is_active:
            raise ValidationError("Cannot assign an inactive level.")

        with transaction.atomic():
            previous_level = self.level
            self.level = level

            # If an agent assigns the level and the user has no agent yet, link them.
            if assigned_by.user_type == 'AGENT' and not self.agent:
                self.agent = assigned_by

            self.save(update_fields=['level', 'agent'])

            LevelAssignment.objects.create(
                user=self,
                assigned_by=assigned_by,
                from_level=previous_level,
                to_level=level
            )

    @staticmethod
    def generate_referral_code(length=8):
        """Generate a unique referral code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not CustomUser.objects.filter(referral_code=code).exists():
                return code
    
    def get_image_limit(self):
        """Get user's image upload limit based on their level"""
        return self.level.image_upload_limit if self.level else 10
    
    def get_commission_rate(self):
        """Get user's commission rate based on their level"""
        return self.level.commission_rate if self.level else 5.00
    
    def can_upload_more_images(self, current_count):
        """Check if user can upload more images"""
        return current_count < self.get_image_limit()
    
    def get_upgrade_options(self):
        """Get available level upgrades for this user"""
        if not self.level:
            return Level.objects.filter(is_active=True).order_by('level_order')
        return Level.objects.filter(
            is_active=True,
            level_order__gt=self.level.level_order
        ).order_by('level_order')


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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
        ordering = ['level__level_order', 'title']
        indexes = [
            models.Index(fields=['level', 'status']),
        ]

    def __str__(self):
        level_name = self.level.display_name if self.level else 'No Level'
        return f"{self.title} ({level_name})"

    def save(self, *args, **kwargs):
        if not self.level:
            default_level = Level.get_default_level()
            if default_level:
                self.level = default_level
        if not self.commission_percentage and self.level:
            self.commission_percentage = self.level.commission_rate

        if self.price is None:
            self.price = Decimal('0.00')

        if self.commission_percentage is None:
            self.commission_percentage = Decimal('0.00')

        if self.commission is None:
            self.commission = (
                (Decimal(self.price) * Decimal(self.commission_percentage)) / Decimal('100')
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        commission_value = self.commission if self.commission is not None else Decimal('0.00')
        self.total_value = (
            Decimal(self.price) + commission_value
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'COMPLETED':
            self.completed_at = None

        super().save(*args, **kwargs)


class LevelUpgrade(models.Model):
    """Track user level upgrades"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        from_name = self.from_level.display_name if self.from_level else 'None'
        return f"{self.user.username}: {from_name} → {self.to_level.display_name}"


class LevelAssignment(models.Model):
    """Keep a history of level assignments performed by agents or super admins."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        from_level_name = self.from_level.display_name if self.from_level else 'None'
        to_level_name = self.to_level.display_name if self.to_level else 'None'
        assigned_by = self.assigned_by.username if self.assigned_by else 'Unknown'
        return f"{self.user.username}: {from_level_name} → {to_level_name} by {assigned_by}"

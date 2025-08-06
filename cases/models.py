# models.py - Improved version
from django.db import models
from accounts.models import CustomUser

class Case(models.Model):
    TYPE_CHOICES = [
        ('general', 'General'),
        ('crypto', 'Crypto'),
        ('money_recovery', 'Money Recovery'),
        ('social_media', 'Social Media'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    agent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases',
        limit_choices_to={'is_agent': True}
    )

    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='customer_cases',
        limit_choices_to={'is_customer': True}
    )

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='normal')
    resolution = models.TextField(blank=True, null=True)
    resolution_date = models.DateTimeField(blank=True, null=True)
    resolution_status = models.CharField(max_length=50, default='unresolved')
    is_active = models.BooleanField(default=True)
    is_closed = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='general')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['type']),
            models.Index(fields=['customer']),
            models.Index(fields=['agent']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
        
    def get_images(self):
        return self.messages.filter(image__isnull=False)

    def get_documents(self):
        return self.messages.filter(document__isnull=False)

    def get_voice_notes(self):
        return self.messages.filter(voice_note__isnull=False)
    
    def close_case(self):
        """Helper method to close a case"""
        self.is_closed = True
        self.status = 'closed'
        self.save()
    
    def assign_agent(self, agent):
        """Helper method to assign an agent"""
        self.agent = agent
        self.status = 'in_progress'
        self.save()


class SupportingDocuments(models.Model):
    file = models.FileField(upload_to='supporting_documents/')
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='supporting_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']


class CryptoLossReport(Case):
    CRYPTO_CHOICES = [
        ("Bitcoin", "Bitcoin"),
        ("Ethereum", "Ethereum"),
        ("USDT", "USDT"),
        ("BNB", "BNB"),
        ("Solana", "Solana"),
        ("Litecoin", "Litecoin"),
        ("Cardano", "Cardano"),
        ("Polkadot", "Polkadot"),
        ("Other", "Other"),
    ]

    amount_lost = models.DecimalField(max_digits=20, decimal_places=8)
    usdt_value = models.DecimalField(max_digits=20, decimal_places=8)
    txid = models.CharField(max_length=255, help_text="Transaction ID")
    sender_wallet = models.CharField(max_length=255)
    receiver_wallet = models.CharField(max_length=255)
    platform_used = models.CharField(max_length=255, blank=True, null=True)
    blockchain_hash = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(max_length=255, blank=True, null=True)
    exchange_info = models.TextField(blank=True, null=True)
    wallet_backup = models.TextField(blank=True, null=True)
    crypto_type = models.CharField(max_length=50, choices=CRYPTO_CHOICES, default="Bitcoin")
    transaction_datetime = models.DateTimeField()
    loss_description = models.TextField()
    
    def save(self, *args, **kwargs):
        self.type = 'crypto'
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Crypto Loss Report"
        verbose_name_plural = "Crypto Loss Reports"


class SocialMediaRecovery(Case):
    PLATFORM_CHOICES = [
        ("Facebook", "Facebook"),
        ("Instagram", "Instagram"),
        ("Twitter", "Twitter"),
        ("LinkedIn", "LinkedIn"),
        ("Snapchat", "Snapchat"),
        ("TikTok", "TikTok"),
        ("Reddit", "Reddit"),
        ("YouTube", "YouTube"),
        ("Pinterest", "Pinterest"),
        ("WhatsApp", "WhatsApp"),
        ("Telegram", "Telegram"),
        ("Discord", "Discord"),
        ("Other", "Other"),
    ]

    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    username = models.CharField(max_length=150)
    profile_url = models.URLField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    account_creation_date = models.DateField(blank=True, null=True)
    last_access_date = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        self.type = 'social_media'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.platform} - {self.username}"
        
    class Meta:
        verbose_name = "Social Media Recovery"
        verbose_name_plural = "Social Media Recoveries"


class MoneyRecoveryReport(Case):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    identification = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    ref_number = models.CharField(max_length=150, blank=True, null=True)
    bank = models.CharField(max_length=150)
    iban = models.CharField(max_length=150)
    datetime = models.DateTimeField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.type = 'money_recovery'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - ${self.amount} lost"
        
    class Meta:
        verbose_name = "Money Recovery Report"
        verbose_name_plural = "Money Recovery Reports"


class MoneyRecoveryFile(models.Model):
    report = models.ForeignKey(
        MoneyRecoveryReport, 
        on_delete=models.CASCADE, 
        related_name='files'
    )
    file = models.FileField(upload_to='money_recovery_files/')
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']

from rest_framework import serializers
from .models import Case, SupportingDocuments, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport, MoneyRecoveryFile
from accounts.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class SupportingDocumentsSerializer(serializers.ModelSerializer):
    file = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = SupportingDocuments
        fields = ['id', 'file', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class CaseSerializer(serializers.ModelSerializer):
    agent = CustomUserSerializer(read_only=True)
    customer = CustomUserSerializer(read_only=True)
    supporting_documents = SupportingDocumentsSerializer(many=True, read_only=True)
    type = serializers.ChoiceField(choices=Case.TYPE_CHOICES)
    status = serializers.ChoiceField(choices=Case.STATUS_CHOICES)
    priority = serializers.ChoiceField(choices=Case.PRIORITY_CHOICES)

    class Meta:
        model = Case
        fields = [
            'id', 'title', 'description', 'created_at', 'updated_at',
            'agent', 'customer', 'status', 'priority', 'resolution',
            'resolution_date', 'resolution_status', 'is_active', 'is_closed',
            'type', 'supporting_documents'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolution_date']

    def validate(self, data):
        if data.get('is_closed') and data.get('status') != 'closed':
            raise serializers.ValidationError("Closed cases must have status 'closed'")
        return data

class CryptoLossReportSerializer(serializers.ModelSerializer):
    agent = CustomUserSerializer(read_only=True)
    customer = CustomUserSerializer(read_only=True)
    supporting_documents = SupportingDocumentsSerializer(many=True, read_only=True)
    crypto_type = serializers.ChoiceField(choices=CryptoLossReport.CRYPTO_CHOICES)

    class Meta:
        model = CryptoLossReport
        fields = [
            'id', 'title', 'description', 'created_at', 'updated_at',
            'agent', 'customer', 'status', 'priority', 'resolution',
            'resolution_date', 'resolution_status', 'is_active', 'is_closed',
            'type', 'supporting_documents', 'amount_lost', 'usdt_value',
            'txid', 'sender_wallet', 'receiver_wallet', 'platform_used',
            'blockchain_hash', 'payment_method', 'exchange_info',
            'wallet_backup', 'crypto_type', 'transaction_datetime',
            'loss_description'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolution_date', 'type']

    def validate(self, data):
        if data.get('amount_lost') <= 0:
            raise serializers.ValidationError("Amount lost must be greater than zero")
        if data.get('usdt_value') <= 0:
            raise serializers.ValidationError("USDT value must be greater than zero")
        return data

class SocialMediaRecoverySerializer(serializers.ModelSerializer):
    agent = CustomUserSerializer(read_only=True)
    customer = CustomUserSerializer(read_only=True)
    supporting_documents = SupportingDocumentsSerializer(many=True, read_only=True)
    platform = serializers.ChoiceField(choices=SocialMediaRecovery.PLATFORM_CHOICES)
    profile_pic = serializers.ImageField(max_length=None, use_url=True, allow_empty_file=True, required=False)

    class Meta:
        model = SocialMediaRecovery
        fields = [
            'id', 'title', 'description', 'created_at', 'updated_at',
            'agent', 'customer', 'status', 'priority', 'resolution',
            'resolution_date', 'resolution_status', 'is_active', 'is_closed',
            'type', 'supporting_documents', 'platform', 'full_name',
            'email', 'phone', 'username', 'profile_url', 'profile_pic',
            'submitted_at', 'account_creation_date', 'last_access_date'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolution_date', 'submitted_at', 'type']

class MoneyRecoveryFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = MoneyRecoveryFile
        fields = ['id', 'file', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class MoneyRecoveryReportSerializer(serializers.ModelSerializer):
    agent = CustomUserSerializer(read_only=True)
    customer = CustomUserSerializer(read_only=True)
    supporting_documents = SupportingDocumentsSerializer(many=True, read_only=True)
    files = MoneyRecoveryFileSerializer(many=True, read_only=True)

    class Meta:
        model = MoneyRecoveryReport
        fields = [
            'id', 'title', 'description', 'created_at', 'updated_at',
            'agent', 'customer', 'status', 'priority', 'resolution',
            'resolution_date', 'resolution_status', 'is_active', 'is_closed',
            'type', 'supporting_documents', 'files', 'first_name', 'last_name',
            'phone', 'email', 'identification', 'amount', 'ref_number',
            'bank', 'iban', 'datetime', 'submitted_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolution_date', 'submitted_at', 'type']

    def validate(self, data):
        if data.get('amount') <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return data

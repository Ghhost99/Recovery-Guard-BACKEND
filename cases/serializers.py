
# serializers.py - Improved version
from rest_framework import serializers
from .models import Case, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport, SupportingDocuments
# Add this to your serializers.py file
from rest_framework import serializers
from .models import SupportingDocuments

class SupportingDocumentsSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportingDocuments
        fields = [
            'id', 
            'file', 
            'file_url', 
            'file_name', 
            'file_size', 
            'description', 
            'uploaded_at', 
            'case'
        ]
        read_only_fields = ['id', 'uploaded_at', 'case']
    
    def get_file_url(self, obj):
        """Get the URL of the uploaded file"""
        if obj.file:
            return obj.file.url
        return None
    
    def get_file_size(self, obj):
        """Get the size of the uploaded file in bytes"""
        if obj.file:
            try:
                return obj.file.size
            except:
                return None
        return None
    
    def get_file_name(self, obj):
        """Get the original name of the uploaded file"""
        if obj.file:
            return obj.file.name.split('/')[-1]  # Get just the filename
        return None

class CaseSerializer(serializers.ModelSerializer):
    supporting_documents = SupportingDocumentsSerializer(many=True, read_only=True)
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id', 'title', 'description', 'status', 'priority', 
            'created_at', 'updated_at', 'type', 'resolution',
            'resolution_date', 'resolution_status', 'is_active',
            'is_closed', 'agent_name', 'customer_name',
            'supporting_documents'
        ]
        read_only_fields = ['created_at', 'updated_at']

class CryptoLossReportSerializer(CaseSerializer):
    class Meta:
        model = CryptoLossReport
        fields = CaseSerializer.Meta.fields + [
            'amount_lost', 'usdt_value', 'txid', 'sender_wallet', 
            'receiver_wallet', 'platform_used', 'blockchain_hash', 
            'payment_method', 'crypto_type', 'transaction_datetime', 
            'loss_description', 'exchange_info', 'wallet_backup'
        ]

class SocialMediaRecoverySerializer(CaseSerializer):
    class Meta:
        model = SocialMediaRecovery
        fields = CaseSerializer.Meta.fields + [
            'platform', 'full_name', 'email', 'phone', 'username', 
            'profile_url', 'profile_pic', 'submitted_at',
            'account_creation_date', 'last_access_date'
        ]

class MoneyRecoveryReportSerializer(CaseSerializer):
    class Meta:
        model = MoneyRecoveryReport
        fields = CaseSerializer.Meta.fields + [
            'first_name', 'last_name', 'phone', 'email', 'identification',
            'amount', 'ref_number', 'bank', 'iban', 'datetime', 'submitted_at'
        ]


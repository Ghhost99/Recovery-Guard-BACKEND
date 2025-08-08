# views.py - Updated version with supporting documents handling
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Case, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport, SupportingDocuments
from .serializers import (
    CaseSerializer, CryptoLossReportSerializer, 
    SocialMediaRecoverySerializer, MoneyRecoveryReportSerializer,
    SupportingDocumentsSerializer
)

class CaseListApiView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retrieve cases based on user role:
        - Customers see only their cases
        - Agents see cases assigned to them or unassigned cases
        """
        user = request.user
        
        # Filter cases based on user role
        if hasattr(user, 'is_customer') and user.is_customer:
            cases = Case.objects.filter(customer=user)
        elif hasattr(user, 'is_agent') and user.is_agent:
            cases = Case.objects.filter(
                Q(agent=user) | Q(agent__isnull=True)
            )
        else:
            return Response(
                {"error": "User role not recognized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Apply filters
        case_status = request.query_params.get('status')
        case_type = request.query_params.get('type')
        priority = request.query_params.get('priority')
        
        if case_status:
            cases = cases.filter(status=case_status)
        if case_type:
            cases = cases.filter(type=case_type)
        if priority:
            cases = cases.filter(priority=priority)
        
        serializer = CaseSerializer(cases, many=True)
        return Response({
            'count': cases.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

def save_supporting_documents(case, files, descriptions=None):
    """
    Helper function to save supporting documents for a case
    """
    saved_documents = []
    
    if not files:
        return saved_documents
    
    # Handle single file or multiple files
    if not isinstance(files, list):
        files = [files]
    
    # Handle descriptions
    if descriptions and not isinstance(descriptions, list):
        descriptions = [descriptions]
    elif not descriptions:
        descriptions = [None] * len(files)
    
    for i, file in enumerate(files):
        if file:  # Check if file is not empty
            description = descriptions[i] if i < len(descriptions) else None
            document = SupportingDocuments.objects.create(
                case=case,
                file=file,
                description=description or f"Supporting document {i+1}"
            )
            saved_documents.append(document)
    
    return saved_documents

class CreateCryptoLossAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        files = request.FILES.getlist('supporting_documents')  # Handle multiple files
        descriptions = request.POST.getlist('document_descriptions')  # Optional descriptions
        
        try:
            with transaction.atomic():
                # Create CryptoLossReport instance directly
                crypto_report = CryptoLossReport(
                    customer=request.user,
                    title=data.get('title', 'Crypto Loss Report'),
                    description=data.get('description', ''),
                    type='crypto',
                    status=data.get('status', 'open'),
                    priority=data.get('priority', 'normal'),
                    
                    # Crypto-specific fields
                    amount_lost=data.get('amount_lost'),
                    usdt_value=data.get('usdt_value'),
                    txid=data.get('txid', ''),
                    sender_wallet=data.get('sender_wallet', ''),
                    receiver_wallet=data.get('receiver_wallet', ''),
                    platform_used=data.get('platform_used', ''),
                    blockchain_hash=data.get('blockchain_hash', ''),
                    payment_method=data.get('payment_method', ''),
                    crypto_type=data.get('crypto_type', ''),
                    transaction_datetime=data.get('transaction_datetime'),
                    loss_description=data.get('loss_description', ''),
                    exchange_info=data.get('exchange_info', ''),
                    wallet_backup=data.get('wallet_backup', False)
                )
                
                # Validate and save
                crypto_report.full_clean()
                crypto_report.save()
                
                # Save supporting documents if provided
                documents = save_supporting_documents(crypto_report, files, descriptions)
                
                # Serialize for response
                serializer = CryptoLossReportSerializer(crypto_report)
                response_data = serializer.data
                
                # Add documents info to response
                if documents:
                    response_data['supporting_documents'] = SupportingDocumentsSerializer(documents, many=True).data
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": e.message_dict}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create crypto loss report", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CreateSocialMediaRecoveryAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        files = request.FILES.getlist('supporting_documents')
        descriptions = request.POST.getlist('document_descriptions')
        
        try:
            with transaction.atomic():
                # Create SocialMediaRecovery instance directly
                social_recovery = SocialMediaRecovery(
                    customer=request.user,
                    title=data.get('title', 'Social Media Recovery Request'),
                    description=data.get('description', ''),
                    type='social_media',
                    status=data.get('status', 'open'),
                    priority=data.get('priority', 'normal'),
                    
                    # Social media specific fields
                    platform=data.get('platform', ''),
                    full_name=data.get('full_name', ''),
                    email=data.get('email', ''),
                    phone=data.get('phone', ''),
                    username=data.get('username', ''),
                    profile_url=data.get('profile_url', ''),
                    profile_pic=data.get('profile_pic'),
                    account_creation_date=data.get('account_creation_date'),
                    last_access_date=data.get('last_access_date')
                )
                
                # Validate and save
                social_recovery.full_clean()
                social_recovery.save()
                
                # Save supporting documents if provided
                documents = save_supporting_documents(social_recovery, files, descriptions)
                
                # Serialize for response
                serializer = SocialMediaRecoverySerializer(social_recovery)
                response_data = serializer.data
                
                # Add documents info to response
                if documents:
                    response_data['supporting_documents'] = SupportingDocumentsSerializer(documents, many=True).data
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": e.message_dict}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create social media recovery request", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CreateMoneyRecoveryAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        files = request.FILES.getlist('supporting_documents')
        descriptions = request.POST.getlist('document_descriptions')
        
        try:
            with transaction.atomic():
                # Create MoneyRecoveryReport instance directly
                money_recovery = MoneyRecoveryReport(
                    customer=request.user,
                    title=data.get('title', 'Money Recovery Report'),
                    description=data.get('description', ''),
                    type='money_recovery',
                    status=data.get('status', 'open'),
                    priority=data.get('priority', 'normal'),
                    
                    # Money recovery specific fields
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    phone=data.get('phone', ''),
                    email=data.get('email', ''),
                    identification=data.get('identification', ''),
                    amount=data.get('amount'),
                    ref_number=data.get('ref_number', ''),
                    bank=data.get('bank', ''),
                    iban=data.get('iban', ''),
                    datetime=data.get('datetime')
                )
                
                # Validate and save
                money_recovery.full_clean()
                money_recovery.save()
                
                # Save supporting documents if provided
                documents = save_supporting_documents(money_recovery, files, descriptions)
                
                # Serialize for response
                serializer = MoneyRecoveryReportSerializer(money_recovery)
                response_data = serializer.data
                
                # Add documents info to response
                if documents:
                    response_data['supporting_documents'] = SupportingDocumentsSerializer(documents, many=True).data
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": e.message_dict}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create money recovery report", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CaseDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        
        # Check permissions
        if not self._has_permission(request.user, case):
            return Response(
                {"error": "You do not have permission to view this case."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the appropriate serializer based on case type
        serializer = self._get_serializer(case)
        response_data = serializer.data
        
        # Add supporting documents to response
        documents = case.supporting_documents.all()
        if documents.exists():
            response_data['supporting_documents'] = SupportingDocumentsSerializer(documents, many=True).data
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        
        # Check permissions
        if not self._has_permission(request.user, case):
            return Response(
                {"error": "You do not have permission to update this case."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        files = request.FILES.getlist('supporting_documents')
        descriptions = request.POST.getlist('document_descriptions')

        try:
            with transaction.atomic():
                # Update fields directly on the model instance
                
                # Update base Case fields
                base_fields = ['title', 'description', 'status', 'priority', 'resolution', 'resolution_status']
                for field in base_fields:
                    if field in data:
                        setattr(case, field, data[field])
                
                # Update type-specific fields based on case type
                if hasattr(case, 'cryptolossreport'):
                    crypto_fields = [
                        'amount_lost', 'usdt_value', 'txid', 'sender_wallet', 
                        'receiver_wallet', 'platform_used', 'blockchain_hash', 
                        'payment_method', 'crypto_type', 'transaction_datetime', 
                        'loss_description', 'exchange_info', 'wallet_backup'
                    ]
                    for field in crypto_fields:
                        if field in data:
                            setattr(case.cryptolossreport, field, data[field])
                    
                elif hasattr(case, 'socialmediarecovery'):
                    social_fields = [
                        'platform', 'full_name', 'email', 'phone', 'username', 
                        'profile_url', 'profile_pic', 'account_creation_date', 'last_access_date'
                    ]
                    for field in social_fields:
                        if field in data:
                            setattr(case.socialmediarecovery, field, data[field])
                
                elif hasattr(case, 'moneyrecoveryreport'):
                    money_fields = [
                        'first_name', 'last_name', 'phone', 'email', 'identification',
                        'amount', 'ref_number', 'bank', 'iban', 'datetime'
                    ]
                    for field in money_fields:
                        if field in data:
                            setattr(case.moneyrecoveryreport, field, data[field])
                
                # Validate and save
                case.full_clean()
                case.save()
                
                # Save related objects if they exist
                if hasattr(case, 'cryptolossreport'):
                    case.cryptolossreport.full_clean()
                    case.cryptolossreport.save()
                elif hasattr(case, 'socialmediarecovery'):
                    case.socialmediarecovery.full_clean()
                    case.socialmediarecovery.save()
                elif hasattr(case, 'moneyrecoveryreport'):
                    case.moneyrecoveryreport.full_clean()
                    case.moneyrecoveryreport.save()
                
                # Save additional supporting documents if provided
                new_documents = []
                if files:
                    new_documents = save_supporting_documents(case, files, descriptions)
                
                # Return serialized response
                serializer = self._get_serializer(case)
                response_data = serializer.data
                
                # Add all supporting documents to response
                all_documents = case.supporting_documents.all()
                if all_documents.exists():
                    response_data['supporting_documents'] = SupportingDocumentsSerializer(all_documents, many=True).data
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": e.message_dict}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to update case", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        
        # Only allow deletion by case owner or assigned agent
        if not self._has_permission(request.user, case):
            return Response(
                {"error": "You do not have permission to delete this case."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        case.delete()  # This will cascade delete supporting documents
        return Response(
            {"message": "Case deleted successfully"}, 
            status=status.HTTP_204_NO_CONTENT
        )
    
    def _has_permission(self, user, case):
        """Check if user has permission to access the case"""
        return (user == case.customer or 
                (case.agent and case.agent == user) or
                (hasattr(user, 'is_agent') and user.is_agent and case.agent is None))
    
    def _get_serializer(self, case, data=None, partial=False):
        """Get the appropriate serializer based on case type"""
        if hasattr(case, 'cryptolossreport'):
            return CryptoLossReportSerializer(
                case.cryptolossreport, data=data, partial=partial
            )
        elif hasattr(case, 'socialmediarecovery'):
            return SocialMediaRecoverySerializer(
                case.socialmediarecovery, data=data, partial=partial
            )
        elif hasattr(case, 'moneyrecoveryreport'):
            return MoneyRecoveryReportSerializer(
                case.moneyrecoveryreport, data=data, partial=partial
            )
        else:
            return CaseSerializer(case, data=data, partial=partial)

class SupportingDocumentsAPIView(APIView):
    """Separate endpoint for managing supporting documents"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, case_pk):
        """Add supporting documents to an existing case"""
        case = get_object_or_404(Case, pk=case_pk)
        
        # Check permissions
        if not (request.user == case.customer or 
                (case.agent and case.agent == request.user) or
                (hasattr(request.user, 'is_agent') and request.user.is_agent and case.agent is None)):
            return Response(
                {"error": "You do not have permission to add documents to this case."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        files = request.FILES.getlist('files')
        descriptions = request.POST.getlist('descriptions')
        
        if not files:
            return Response(
                {"error": "No files provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            documents = save_supporting_documents(case, files, descriptions)
            serializer = SupportingDocumentsSerializer(documents, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": "Failed to save documents", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, case_pk, document_pk):
        """Delete a specific supporting document"""
        case = get_object_or_404(Case, pk=case_pk)
        document = get_object_or_404(SupportingDocuments, pk=document_pk, case=case)
        
        # Check permissions
        if not (request.user == case.customer or 
                (case.agent and case.agent == request.user)):
            return Response(
                {"error": "You do not have permission to delete this document."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.delete()
        return Response(
            {"message": "Document deleted successfully"}, 
            status=status.HTTP_204_NO_CONTENT
        )

class CaseStatsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get case statistics for the current user"""
        user = request.user
        
        if hasattr(user, 'is_customer') and user.is_customer:
            cases = Case.objects.filter(customer=user)
        elif hasattr(user, 'is_agent') and user.is_agent:
            cases = Case.objects.filter(agent=user)
        else:
            return Response(
                {"error": "User role not recognized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_cases': cases.count(),
            'open_cases': cases.filter(status='open').count(),
            'in_progress_cases': cases.filter(status='in_progress').count(),
            'resolved_cases': cases.filter(status='resolved').count(),
            'closed_cases': cases.filter(status='closed').count(),
            'by_type': {
                'crypto': cases.filter(type='crypto').count(),
                'money_recovery': cases.filter(type='money_recovery').count(),
                'social_media': cases.filter(type='social_media').count(),
                'general': cases.filter(type='general').count(),
            },
            'by_priority': {
                'urgent': cases.filter(priority='urgent').count(),
                'high': cases.filter(priority='high').count(),
                'normal': cases.filter(priority='normal').count(),
                'low': cases.filter(priority='low').count(),
            }
        }
        
        return Response(stats, status=status.HTTP_200_OK)
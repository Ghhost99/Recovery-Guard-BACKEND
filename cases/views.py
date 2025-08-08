from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Case, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport, SupportingDocuments
from .serializers import (
    CaseSerializer, CryptoLossReportSerializer, 
    SocialMediaRecoverySerializer, MoneyRecoveryReportSerializer,
    SupportingDocumentsSerializer
)

def save_supporting_documents(case, files, descriptions=None):
    """Helper function to save supporting documents"""
    documents = []
    
    if not files:
        return documents
    
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
            document = SupportingDocuments(
                case=case,
                file=file,
                description=description or f"Supporting document {i+1}"
            )
            document.full_clean()
            document.save()
            documents.append(document)
    
    return documents

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

class CreateCryptoLossAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new CryptoLossReport"""
        data = request.data.copy()
        data['customer'] = request.user.id  # Set customer to current user
        files = request.FILES.getlist('supporting_documents')
        descriptions = request.POST.getlist('document_descriptions')
        
        try:
            with transaction.atomic():
                serializer = CryptoLossReportSerializer(data=data)
                if serializer.is_valid():
                    crypto_report = serializer.save()
                    
                    # Save supporting documents if provided
                    if files:
                        documents = save_supporting_documents(crypto_report, files, descriptions)
                        serializer = CryptoLossReportSerializer(crypto_report)  # Refresh serializer
                        response_data = serializer.data
                    else:
                        response_data = serializer.data
                        
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {"error": "Validation error", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": str(e)},
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
        """Create a new SocialMediaRecovery"""
        data = request.data.copy()
        data['customer'] = request.user.id
        files = request.FILES.getlist('supporting_documents')
        descriptions = request.POST.getlist('document_descriptions')
        
        try:
            with transaction.atomic():
                serializer = SocialMediaRecoverySerializer(data=data)
                if serializer.is_valid():
                    social_recovery = serializer.save()
                    
                    # Save supporting documents if provided
                    if files:
                        documents = save_supporting_documents(social_recovery, files, descriptions)
                        serializer = SocialMediaRecoverySerializer(social_recovery)
                        response_data = serializer.data
                    else:
                        response_data = serializer.data
                        
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {"error": "Validation error", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": str(e)},
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
        """Create a new MoneyRecoveryReport"""
        data = request.data.copy()
        data['customer'] = request.user.id
        files = request.FILES.getlist('supporting_documents')
        descriptions = request.POST.getlist('document_descriptions')
        
        try:
            with transaction.atomic():
                serializer = MoneyRecoveryReportSerializer(data=data)
                if serializer.is_valid():
                    money_recovery = serializer.save()
                    
                    # Save supporting documents if provided
                    if files:
                        documents = save_supporting_documents(money_recovery, files, descriptions)
                        serializer = MoneyRecoveryReportSerializer(money_recovery)
                        response_data = serializer.data
                    else:
                        response_data = serializer.data
                        
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {"error": "Validation error", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
        except ValidationError as e:
            return Response(
                {"error": "Validation error", "details": str(e)},
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
        """Retrieve case details"""
        with transaction.atomic():
            case = get_object_or_404(Case, pk=pk)
            
            # Check permissions
            if not self._has_permission(request.user, case):
                return Response(
                    {"error": "You do not have permission to view this case."}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self._get_serializer(case)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """Update case details"""
        with transaction.atomic():
            case = get_object_or_404(Case, pk=pk)
            
            # Check permissions
            if not self._has_permission(request.user, case):
                return Response(
                    {"error": "You do not have permission to update this case."}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get files and descriptions
            files = request.FILES.getlist('supporting_documents')
            descriptions = request.POST.getlist('document_descriptions')
            
            try:
                # Get appropriate serializer
                serializer = self._get_serializer(case, data=request.data, partial=True)
                
                if serializer.is_valid():
                    # Save the case instance
                    instance = serializer.save()
                    
                    # Handle supporting documents
                    if files:
                        new_documents = save_supporting_documents(case, files, descriptions)
                        serializer = self._get_serializer(case)  # Refresh serializer
                        response_data = serializer.data
                    else:
                        response_data = serializer.data

                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"error": "Validation error", "details": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except ValidationError as e:
                return Response(
                    {"error": "Validation error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"error": "Failed to update case", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    def delete(self, request, pk):
        """Delete a case"""
        with transaction.atomic():
            case = get_object_or_404(Case, pk=pk)
            
            # Check permissions
            if not self._has_permission(request.user, case):
                return Response(
                    {"error": "You do not have permission to delete this case."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            case.delete()
            return Response(
                {"message": "Case deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
    
    def _has_permission(self, user, case):
        """Check if user has permission to access the case"""
        return (
            user == case.customer or
            (case.agent and case.agent == user) or
            (hasattr(user, 'is_agent') and user.is_agent)
        )
    
    def _get_serializer(self, case, data=None, partial=False):
        """Get appropriate serializer based on case type"""
        if hasattr(case, 'cryptolossreport'):
            return CryptoLossReportSerializer(
                instance=case.cryptolossreport, data=data, partial=partial
            )
        elif hasattr(case, 'socialmediarecovery'):
            return SocialMediaRecoverySerializer(
                instance=case.socialmediarecovery, data=data, partial=partial
            )
        elif hasattr(case, 'moneyrecoveryreport'):
            return MoneyRecoveryReportSerializer(
                instance=case.moneyrecoveryreport, data=data, partial=partial
            )
        return CaseSerializer(instance=case, data=data, partial=partial)

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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Case, SupportingDocuments
from .serializers import (
    CaseSerializer, 
    CryptoLossReportSerializer, 
    SocialMediaRecoverySerializer, 
    MoneyRecoveryReportSerializer, 
    SupportingDocumentsSerializer
)

def save_supporting_documents(case, files, descriptions):
    """Helper function to save supporting documents"""
    documents = []
    for file, desc in zip(files, descriptions or []):
        document = SupportingDocuments(
            case=case,
            file=file,
            description=desc or None
        )
        document.full_clean()
        document.save()
        documents.append(document)
    return documents

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
            response_data = serializer.data  # Direct access is fine since no input data
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

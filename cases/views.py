# views.py - Improved version
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.db.models import Q
from .models import Case, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport
from .serializers import (
    CaseSerializer, CryptoLossReportSerializer, 
    SocialMediaRecoverySerializer, MoneyRecoveryReportSerializer
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

class CreateCryptoLossAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data.copy()
        data['customer'] = request.user.id
        
        serializer = CryptoLossReportSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateSocialMediaRecoveryAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data.copy()
        data['customer'] = request.user.id
        
        serializer = SocialMediaRecoverySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateMoneyRecoveryAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data.copy()
        data['customer'] = request.user.id
        
        serializer = MoneyRecoveryReportSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        
        # Check permissions
        if not self._has_permission(request.user, case):
            return Response(
                {"error": "You do not have permission to update this case."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self._get_serializer(case, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        
        # Only allow deletion by case owner or assigned agent
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
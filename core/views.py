# views.py - Dashboard API using DRF Class-Based Views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from cases.models import Case, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport, SupportingDocuments
from accounts.models import CustomUser
from notifications.models import Notification


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class DashboardView(APIView):
    """
    Comprehensive dashboard API that provides stats, progress, and activity data
    based on user role (customer, agent, or admin)
    """
    permission_classes = [IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def post(self, request):
        user = request.user
        
        # Filter cases based on user role
        if user.is_customer:
            user_cases = Case.objects.filter(customer=user, is_active=True)
            role = 'customer'
        elif user.is_agent:
            user_cases = Case.objects.filter(agent=user, is_active=True)
            role = 'agent'
        else:
            # Admin or staff can see all cases
            user_cases = Case.objects.filter(is_active=True)
            role = 'admin'
        
        # Get case type specific querysets
        crypto_cases = user_cases.filter(type='crypto')
        social_cases = user_cases.filter(type='social_media')
        money_cases = user_cases.filter(type='money_recovery')
        general_cases = user_cases.filter(type='general')
        
        # Build stats
        stats = self._build_stats(user_cases, crypto_cases, social_cases, money_cases, general_cases, role, user)
        
        # Build progress
        progress = self._build_progress(user_cases)
        
        # Build activity
        activity = self._build_activity(user_cases)
        
        # Prepare response data
        response_data = {
            "stats": stats,
            "progress": progress,
            "activity": activity,
            "user_role": role,
            "summary": {
                "total_cases": user_cases.count(),
                "case_types": {
                    "crypto": crypto_cases.count(),
                    "social_media": social_cases.count(),
                    "money_recovery": money_cases.count(),
                    "general": general_cases.count()
                },
                "status_breakdown": {
                    "open": user_cases.filter(status='open').count(),
                    "in_progress": user_cases.filter(status='in_progress').count(),
                    "pending": user_cases.filter(status='pending').count(),
                    "resolved": user_cases.filter(status='resolved').count(),
                    "closed": user_cases.filter(status='closed').count()
                }
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _build_stats(self, user_cases, crypto_cases, social_cases, money_cases, general_cases, role, user):
        """Build comprehensive stats array"""
        stats = []
        
        # Total cases by status
        stats.extend([
            {
                "label": "Total Cases",
                "value": str(user_cases.count())
            },
            {
                "label": "Open Cases", 
                "value": str(user_cases.filter(status='open').count())
            },
            {
                "label": "In Progress",
                "value": str(user_cases.filter(status='in_progress').count())
            },
            {
                "label": "Resolved",
                "value": str(user_cases.filter(status='resolved').count())
            }
        ])
        
        # Case type breakdown
        if role != 'customer' or user_cases.count() > 0:
            stats.extend([
                {
                    "label": "Crypto Cases",
                    "value": str(crypto_cases.count())
                },
                {
                    "label": "Social Media",
                    "value": str(social_cases.count())
                },
                {
                    "label": "Money Recovery",
                    "value": str(money_cases.count())
                },
                {
                    "label": "General Cases",
                    "value": str(general_cases.count())
                }
            ])
        
        # Priority breakdown
        urgent_cases = user_cases.filter(priority='urgent').count()
        high_cases = user_cases.filter(priority='high').count()
        
        if urgent_cases > 0 or high_cases > 0:
            stats.extend([
                {
                    "label": "Urgent Cases",
                    "value": str(urgent_cases)
                },
                {
                    "label": "High Priority",
                    "value": str(high_cases)
                }
            ])
        
        # Financial stats for money and crypto cases
        try:
            # Crypto losses
            crypto_reports = CryptoLossReport.objects.filter(
                id__in=crypto_cases.values('id')
            )
            total_crypto_usdt = crypto_reports.aggregate(
                total=Sum('usdt_value')
            )['total'] or Decimal('0')
            
            if total_crypto_usdt > 0:
                stats.append({
                    "label": "Crypto Loss (USDT)",
                    "value": f"${total_crypto_usdt:,.2f}"
                })
            
            # Money recovery amounts
            money_reports = MoneyRecoveryReport.objects.filter(
                id__in=money_cases.values('id')
            )
            total_money_lost = money_reports.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            if total_money_lost > 0:
                stats.append({
                    "label": "Money Lost",
                    "value": f"${total_money_lost:,.2f}"
                })
                
        except Exception as e:
            # Handle any aggregation errors gracefully
            pass
        
        # Add notifications count if available
        try:
            unread_notifications = Notification.objects.filter(
                recipient=user, 
                is_read=False
            ).count()
            
            if unread_notifications > 0:
                stats.append({
                    "label": "Notifications",
                    "value": str(unread_notifications)
                })
        except Exception:
            pass
        
        return stats
    
    def _build_progress(self, user_cases):
        """Build progress tracking based on case resolution pipeline"""
        total_cases = user_cases.count()
        
        if total_cases > 0:
            # Define progress steps
            progress_steps = [
                "Case Created", 
                "Under Review", 
                "Investigation", 
                "Resolution Phase", 
                "Completed"
            ]
            
            # Calculate progress based on case statuses
            open_count = user_cases.filter(status='open').count()
            in_progress_count = user_cases.filter(status='in_progress').count()
            pending_count = user_cases.filter(status='pending').count()
            resolved_count = user_cases.filter(status__in=['resolved', 'closed']).count()
            
            # Determine current step based on case distribution
            if resolved_count / total_cases >= 0.8:
                current_step_index = 4  # Completed
            elif (resolved_count + pending_count) / total_cases >= 0.6:
                current_step_index = 3  # Resolution Phase
            elif in_progress_count / total_cases >= 0.4:
                current_step_index = 2  # Investigation
            elif open_count < total_cases * 0.8:
                current_step_index = 1  # Under Review
            else:
                current_step_index = 0  # Case Created
                
        else:
            progress_steps = ["No Cases", "Create Case", "Submit Details", "Await Assignment", "In Progress"]
            current_step_index = 0
        
        return {
            "steps": progress_steps,
            "currentStepIndex": current_step_index
        }
    
    def _build_activity(self, user_cases):
        """Build recent activity feed"""
        activity = []
        
        # Get recent case updates (last 15 cases)
        recent_cases = user_cases.order_by('-updated_at')[:15]
        
        for case in recent_cases:
            # Determine activity icon based on case type and status
            if case.type == 'crypto':
                icon = "₿"
            elif case.type == 'social_media':
                icon = "📱"
            elif case.type == 'money_recovery':
                icon = "💰"
            else:
                icon = "📋"
            
            # Create activity message based on status
            if case.status == 'resolved':
                message = f"Case resolved: {case.title}"
                detail = "✅ Completed"
            elif case.status == 'in_progress':
                message = f"Case in progress: {case.title}"
                detail = f"Assigned to {case.agent.first_name if case.agent else 'Unassigned'}"
            elif case.status == 'pending':
                message = f"Case pending: {case.title}"
                detail = "⏳ Awaiting action"
            elif case.status == 'open':
                message = f"New case opened: {case.title}"
                detail = "🆕 Recently created"
            else:
                message = f"Case updated: {case.title}"
                detail = case.get_status_display()
            
            # Calculate time ago
            time_diff = timezone.now() - case.updated_at
            time_ago = self._calculate_time_ago(time_diff)
            
            activity.append({
                "icon": icon,
                "message": message,
                "detail": detail,
                "time": time_ago,
                "case_id": case.id,
                "case_type": case.get_type_display(),
                "priority": case.priority
            })
        
        # Add recent document uploads to activity
        try:
            recent_docs = SupportingDocuments.objects.filter(
                case__in=user_cases
            ).order_by('-uploaded_at')[:5]
            
            for doc in recent_docs:
                time_diff = timezone.now() - doc.uploaded_at
                time_ago = self._calculate_time_ago(time_diff)
                
                activity.append({
                    "icon": "📎",
                    "message": f"Document uploaded for case: {doc.case.title}",
                    "detail": doc.description or "Supporting document",
                    "time": time_ago,
                    "case_id": doc.case.id
                })
        except Exception:
            pass
        
        # Sort activity by most recent first and limit to 10
        return activity[:10]
    
    def _calculate_time_ago(self, time_diff):
        """Calculate human-readable time ago string"""
        if time_diff.days > 0:
            return f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class CaseTypeStatsView(APIView):
    """Get detailed stats for a specific case type"""
    permission_classes = [IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    def get(self, request, case_type=None):
        user = request.user
        
        if user.is_customer:
            base_query = Case.objects.filter(customer=user, is_active=True)
        elif user.is_agent:
            base_query = Case.objects.filter(agent=user, is_active=True)
        else:
            base_query = Case.objects.filter(is_active=True)
        
        if case_type:
            cases = base_query.filter(type=case_type)
        else:
            cases = base_query
        
        stats = {
            "total": cases.count(),
            "case_type": case_type,
            "by_status": {
                "open": cases.filter(status='open').count(),
                "in_progress": cases.filter(status='in_progress').count(),
                "pending": cases.filter(status='pending').count(),
                "resolved": cases.filter(status='resolved').count(),
                "closed": cases.filter(status='closed').count(),
            },
            "by_priority": {
                "low": cases.filter(priority='low').count(),
                "normal": cases.filter(priority='normal').count(),
                "high": cases.filter(priority='high').count(),
                "urgent": cases.filter(priority='urgent').count(),
            }
        }
        
        # Add case type specific stats
        if case_type == 'crypto':
            crypto_reports = CryptoLossReport.objects.filter(id__in=cases.values('id'))
            stats['financial'] = {
                "total_usdt_lost": str(crypto_reports.aggregate(total=Sum('usdt_value'))['total'] or 0),
                "avg_loss_per_case": str(crypto_reports.aggregate(avg=Avg('usdt_value'))['avg'] or 0),
                "crypto_breakdown": list(crypto_reports.values('crypto_type').annotate(count=Count('crypto_type')))
            }
        
        elif case_type == 'money_recovery':
            money_reports = MoneyRecoveryReport.objects.filter(id__in=cases.values('id'))
            stats['financial'] = {
                "total_money_lost": str(money_reports.aggregate(total=Sum('amount'))['total'] or 0),
                "avg_loss_per_case": str(money_reports.aggregate(avg=Avg('amount'))['avg'] or 0),
            }
        
        elif case_type == 'social_media':
            social_reports = SocialMediaRecovery.objects.filter(id__in=cases.values('id'))
            stats['platform_breakdown'] = list(
                social_reports.values('platform').annotate(count=Count('platform'))
            )
        
        return Response(stats, status=status.HTTP_200_OK)


class CaseAnalyticsView(APIView):
    """Advanced analytics for cases"""
    permission_classes = [IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    def get(self, request):
        user = request.user
        
        # Get user's cases based on role
        if user.is_customer:
            user_cases = Case.objects.filter(customer=user, is_active=True)
        elif user.is_agent:
            user_cases = Case.objects.filter(agent=user, is_active=True)
        else:
            user_cases = Case.objects.filter(is_active=True)
        
        # Time-based analytics
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        analytics = {
            "time_analysis": {
                "cases_created_last_30_days": user_cases.filter(created_at__gte=last_30_days).count(),
                "cases_created_last_7_days": user_cases.filter(created_at__gte=last_7_days).count(),
                "cases_resolved_last_30_days": user_cases.filter(
                    resolution_date__gte=last_30_days,
                    status='resolved'
                ).count(),
            },
            "efficiency_metrics": {
                "avg_resolution_time_days": self._calculate_avg_resolution_time(user_cases),
                "resolution_rate": self._calculate_resolution_rate(user_cases),
            },
            "trends": {
                "most_common_case_type": self._get_most_common_case_type(user_cases),
                "priority_distribution": self._get_priority_distribution(user_cases),
            }
        }
        
        return Response(analytics, status=status.HTTP_200_OK)
    
    def _calculate_avg_resolution_time(self, cases):
        """Calculate average resolution time in days"""
        resolved_cases = cases.filter(status='resolved', resolution_date__isnull=False)
        if not resolved_cases.exists():
            return 0
        
        total_days = 0
        count = 0
        
        for case in resolved_cases:
            if case.resolution_date and case.created_at:
                days = (case.resolution_date - case.created_at).days
                total_days += days
                count += 1
        
        return round(total_days / count, 1) if count > 0 else 0
    
    def _calculate_resolution_rate(self, cases):
        """Calculate percentage of resolved cases"""
        total = cases.count()
        if total == 0:
            return 0
        resolved = cases.filter(status='resolved').count()
        return round((resolved / total) * 100, 1)
    
    def _get_most_common_case_type(self, cases):
        """Get the most common case type"""
        type_counts = cases.values('type').annotate(count=Count('type')).order_by('-count')
        if type_counts:
            return {
                "type": type_counts[0]['type'],
                "count": type_counts[0]['count']
            }
        return None
    
    def _get_priority_distribution(self, cases):
        """Get priority distribution"""
        return list(cases.values('priority').annotate(count=Count('priority')))



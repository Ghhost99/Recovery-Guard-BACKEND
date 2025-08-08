from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from cases.models import Case, CryptoLossReport, SocialMediaRecovery, MoneyRecoveryReport, SupportingDocuments

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user

        total_cases = Case.objects.filter(user=user).count()
        total_crypto_cases = Case.objects.filter(user=user, type='crypto').count()
        total_social_media_cases = Case.objects.filter(user=user, type='social_media').count()
        total_money_cases = Case.objects.filter(user=user, type='money').count()

        crypto_cases = Case.objects.filter(user=user, type='crypto')
        social_media_cases = Case.objects.filter(user=user, type='social_media')
        money_cases = Case.objects.filter(user=user, type='money')

        crypto_reports = CryptoLossReport.objects.filter(case__in=crypto_cases)
        social_media_reports = SocialMediaRecovery.objects.filter(case__in=social_media_cases)
        money_reports = MoneyRecoveryReport.objects.filter(case__in=money_cases)

        total_crypto_loss = crypto_reports.aggregate(total=Sum('estimated_loss')).get('total') or 0
        total_money_loss = money_reports.aggregate(total=Sum('amount_lost')).get('total') or 0
        total_money_recovered = money_reports.aggregate(total=Sum('amount_recovered')).get('total') or 0

        recent_activities = self._build_activity(user)

        response_data = {
            'total_cases': total_cases,
            'total_crypto_cases': total_crypto_cases,
            'total_social_media_cases': total_social_media_cases,
            'total_money_cases': total_money_cases,
            'total_crypto_loss': float(total_crypto_loss),
            'total_money_loss': float(total_money_loss),
            'total_money_recovered': float(total_money_recovered),
            'recent_activities': recent_activities,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _build_activity(self, user):
        recent_cases = Case.objects.filter(user=user).order_by('-updated_at')[:5]
        recent_documents = SupportingDocuments.objects.filter(case__user=user).order_by('-uploaded_at')[:5]

        activity = []

        for case in recent_cases:
            activity.append({
                'type': 'Case',
                'title': case.title,
                'description': case.description[:50],
                'time': case.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': case.updated_at.timestamp()
            })

        for doc in recent_documents:
            activity.append({
                'type': 'Document',
                'title': doc.file.name,
                'description': doc.description[:50] if doc.description else '',
                'time': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': doc.uploaded_at.timestamp()
            })

        # Sort all by timestamp descending
        activity.sort(key=lambda x: x['timestamp'], reverse=True)
        return activity[:10]


class CaseTypeStatsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        cases = Case.objects.filter(user=user)

        case_stats = cases.values('type').annotate(count=Count('id'))

        type_mapping = dict(Case.CASE_TYPE_CHOICES)

        response_data = [
            {
                'type': type_mapping.get(stat['type'], stat['type']),
                'count': stat['count']
            }
            for stat in case_stats
        ]

        return Response(response_data, status=status.HTTP_200_OK)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    HealthCheckView,
    DashboardView,
    CaseTypeStatsView,
    CaseAnalyticsView,
)

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health_check'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/notification/', include('notifications.urls')),
    path('api/cases/', include('cases.urls')),
    path('api/chat/', include('chat.urls')),

    # ✅ Custom API views
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/case-stats/', CaseTypeStatsView.as_view(), name='case_type_stats'),
    path('api/case-stats/<str:case_type>/', CaseTypeStatsView.as_view(), name='case_type_stats_filtered'),
    path('api/case-analytics/', CaseAnalyticsView.as_view(), name='case_analytics'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

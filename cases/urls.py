from django.urls import path
from .views import *
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # Case listing and stats
    path('cases/', CaseListApiView.as_view(), name='case-list'),
    path('cases/stats/', CaseStatsAPIView.as_view(), name='case-stats'),
    
    # Case detail operations (GET, PUT, DELETE)
    path('cases/<int:pk>/', CaseDetailView.as_view(), name='case-detail'),
    
    # Case creation endpoints
    path('cases/crypto/', CreateCryptoLossAPIView.as_view(), name='create-crypto-case'),
    path('cases/social-media/', CreateSocialMediaRecoveryAPIView.as_view(), name='create-social-media-case'),
    path('cases/money-recovery/', CreateMoneyRecoveryAPIView.as_view(), name='create-money-recovery-case'),
]
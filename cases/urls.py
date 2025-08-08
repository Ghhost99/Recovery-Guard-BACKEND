from django.urls import path
from .views import (
    CaseListApiView,
    CreateCryptoLossAPIView,
    CreateSocialMediaRecoveryAPIView,
    CreateMoneyRecoveryAPIView,
    CaseDetailView,
    SupportingDocumentsAPIView,
    CaseStatsAPIView
)

urlpatterns = [
    # Case listing and stats
    path('cases/', CaseListApiView.as_view(), name='case-list'),
    path('cases/stats/', CaseStatsAPIView.as_view(), name='case-stats'),
    
    # Case detail operations (GET, PUT, DELETE)
    path('cases/<int:pk>/', CaseDetailView.as_view(), name='case-detail'),

    # Case creation endpoints
    path('cases/crypto/', CreateCryptoLossAPIView.as_view(), name='create-crypto-loss'),
    path('cases/social-media/', CreateSocialMediaRecoveryAPIView.as_view(), name='create-social-recovery'),
    path('cases/money-recovery/', CreateMoneyRecoveryAPIView.as_view(), name='create-money-recovery'),
    
    # Supporting document endpoints
    path('cases/<int:case_pk>/documents/', SupportingDocumentsAPIView.as_view(), name='case-documents'),
    path('cases/<int:case_pk>/documents/<int:document_pk>/', SupportingDocumentsAPIView.as_view(), name='case-document-detail'),
]

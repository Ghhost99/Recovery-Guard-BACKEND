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
    path('', CaseListApiView.as_view(), name='case-list'),
    path('stats/', CaseStatsAPIView.as_view(), name='case-stats'),
    
    # Case detail operations (GET, PUT, DELETE)
    path('<int:pk>/', CaseDetailView.as_view(), name='case-detail'),

    # Case creation endpoints
    path('crypto/', CreateCryptoLossAPIView.as_view(), name='create-crypto-loss'),
    path('social-media/', CreateSocialMediaRecoveryAPIView.as_view(), name='create-social-recovery'),
    path('money-recovery/', CreateMoneyRecoveryAPIView.as_view(), name='create-money-recovery'),
    
    # Supporting document endpoints
    path('<int:case_pk>/documents/', SupportingDocumentsAPIView.as_view(), name='case-documents'),
    path('<int:case_pk>/documents/<int:document_pk>/', SupportingDocumentsAPIView.as_view(), name='case-document-detail'),
]

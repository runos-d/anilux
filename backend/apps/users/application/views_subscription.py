from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

class SubscriptionView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"is_active": True, "is_premium": False, "message": "All features free"})

class SubscriptionActivateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        return Response({"message": "All features free", "is_active": True})

class PromoCodeValidateView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"valid": False, "message": "Promo codes disabled"})

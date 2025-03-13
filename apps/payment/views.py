from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import User, Test, Payment
from apps.multilevel.models import UserTest
from .serializers import PaymentSerializer
import requests

# Payment Initiation View
class InitiatePaymentView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        test_id = request.data.get('test_id')
        amount = request.data.get('amount')

        try:
            user = User.objects.get(id=user_id)
            test = Test.objects.get(id=test_id)
        except (User.DoesNotExist, Test.DoesNotExist):
            return Response({"error": "User or Test not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create a payment record
        payment = Payment.objects.create(user=user, test=test, amount=amount, status='pending')

        # Call Payme API to initiate payment
        payme_url = "https://payme.uz/api/payment/initiate"
        payload = {
            "user_id": user_id,
            "test_id": test_id,
            "amount": amount,
            "callback_url": "https://turantalim.uz/payments/webhook/"  # Webhook for payment confirmation
        }
        headers = {
            "Authorization": "Bearer YOUR_PAYME_API_KEY"
        }

        response = requests.post(payme_url, json=payload, headers=headers)
        if response.status_code == 200:
            payment.payment_url = response.json().get('payment_url')
            payment.save()
            return Response({
                "status": "pending",
                "payment_url": payment.payment_url
            })
        else:
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

# Payment Webhook View
class PaymentWebhookView(APIView):
    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        payment_status = request.data.get('status')
        user_id = request.data.get('user_id')
        test_id = request.data.get('test_id')

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if payment_status == "completed":
            payment.status = "completed"
            payment.save()

            # Grant test access to the user
            UserTest.objects.create(user_id=user_id, test_id=test_id, status="started")

            return Response({"message": "Payment confirmed. Test access granted."})
        else:
            return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

class InitiateClickPaymentView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        test_id = request.data.get('test_id')
        amount = request.data.get('amount')

        try:
            user = User.objects.get(id=user_id)
            test = Test.objects.get(id=test_id)
        except (User.DoesNotExist, Test.DoesNotExist):
            return Response({"error": "User or Test not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create a payment record
        payment = Payment.objects.create(user=user, test=test, amount=amount, status='pending')

        # Call Click API to initiate payment
        click_url = "https://click.uz/api/payment/initiate"
        payload = {
            "user_id": user_id,
            "test_id": test_id,
            "amount": amount,
            "callback_url": "https://turantalim.uz/click/webhook/"  # Webhook for payment confirmation
        }
        headers = {
            "Authorization": "Bearer YOUR_CLICK_API_KEY"
        }

        response = requests.post(click_url, json=payload, headers=headers)
        if response.status_code == 200:
            payment.payment_url = response.json().get('payment_url')
            payment.save()
            return Response({
                "status": "pending",
                "payment_url": payment.payment_url
            })
        else:
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

class ClickWebhookView(APIView):
    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        payment_status = request.data.get('status')
        user_id = request.data.get('user_id')
        test_id = request.data.get('test_id')

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if payment_status == "completed":
            payment.status = "completed"
            payment.save()

            # Grant test access to the user
            UserTest.objects.create(user_id=user_id, test_id=test_id, status="started")

            return Response({"message": "Payment confirmed. Test access granted."})
        else:
            return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
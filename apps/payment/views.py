from rest_framework import views
from rest_framework.response import Response

from payme import Payme
from payme.views import PaymeWebHookAPIView
from payme.models import PaymeTransactions
from payme.types import response

from apps.payment.models import ExamPayment
from apps.multilevel.models import Exam
from .serializers import PaymentSerializer
from core.settings import base

import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# pylint: disable=E1101
class PaymeCallBackAPIView(PaymeWebHookAPIView):
    """
    A view to handle Payme Webhook API calls.
    This view will handle all the Payme Webhook API events.
    """
    def check_perform_transaction(self, params):
        account = self.fetch_account(params)
        self.validate_amount(account, params.get('amount'))

        result = response.CheckPerformTransaction(allow=True)

        exam = Exam.objects.get(id=account.exam.id)
        item = response.Item(
            title=f"{exam.title}",  
            price=int(exam.price * 100),  
            count=1, 
            code=10899002001000000,  
            discount=0,  
            vat_percent=0,
        )
        result.add_item(item)
        return result.as_resp()

    TELEGRAM_BOT_TOKEN = base.TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID = base.TELEGRAM_CHAT_ID 

    def send_telegram_message(self, text):
        """Telegram guruhga xabar yuborish funksiyasi"""
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": self.TELEGRAM_CHAT_ID, "text": text}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram xabar yuborishda xato: {response.text}")

    def handle_successfully_payment(self, params, result, *args, **kwargs):
        """
        Handle the successful payment and send Telegram notification.
        """
        transaction = PaymeTransactions.get_by_transaction_id(
            transaction_id=params["id"]
        )

        order = ExamPayment.objects.get(id=transaction.account_id)
        order.is_paid = True
        order.save()

        # Telegram guruhga xabar yuborish
        message = (
            f"✅ To‘lov tasdiqlandi!\n"
            f"👤 Foydalanuvchi: {order.user.first_name} {order.user.last_name}\n"
            f"📖 Imtihon: {order.exam.title}\n"
            f"💰 To‘lov summasi: {order.amount} UZS\n"
            f"🕒 Sana: {order.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_telegram_message(message)

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        """
        Handle the cancelled payment. You can override this method
        """
        transaction = PaymeTransactions.get_by_transaction_id(
            transaction_id=params["id"]
        )

        if transaction.state == PaymeTransactions.CANCELED:
            order = ExamPayment.objects.get(id=transaction.account_id)
            order.is_paid = False
            order.save()


################################################################

payme = Payme(
    payme_id=base.PAYME_ID
)

class ExamPaymentAPIView(views.APIView):
    serializer_class = PaymentSerializer

    def post(self, request):
        """
        Create a new order.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        result = {
            "order": serializer.data
        }
    
        if serializer.data["payment_method"] == "payme":
            payment_link = payme.initializer.generate_pay_link(
                id=serializer.data["id"],
                amount=serializer.data["amount"],
                return_url="https://uzum.uz"
            )
            result["payment_link"] = payment_link

        return Response(result)
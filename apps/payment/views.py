from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payme import Payme
from payme.views import PaymeWebHookAPIView
from payme.models import PaymeTransactions
from payme.types import response
from apps.payment.models import ExamPayment, UserBalance, BalanceTransaction
from apps.multilevel.models import Exam
from .serializers import PaymentSerializer, BalanceTopUpSerializer, BalanceSerializer, BalanceTransactionSerializer
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

        try:
            # First try to find BalanceTransaction
            balance_topup = BalanceTransaction.objects.get(id=account.id)
            item = response.Item(
                title=f"Balans To'ldirish - {balance_topup.user.username}",
                price=int(balance_topup.amount * 100),
                count=1,
                code=10899002001000001,
                discount=0,
                vat_percent=0,
            )
        except BalanceTransaction.DoesNotExist:
            # If not found, try ExamPayment
            try:
                exam_payment = ExamPayment.objects.get(id=account.id)
                item = response.Item(
                    title=f"Imtihon To'lovi - {exam_payment.exam.title}",
                    price=int(exam_payment.amount * 100),
                    count=1,
                    code=10899002001000002,
                    discount=0,
                    vat_percent=0,
                )
            except ExamPayment.DoesNotExist:
                raise ValueError("Account not found")

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
        transaction = PaymeTransactions.get_by_transaction_id(
            transaction_id=params["id"]
        )

        try:
            # First try BalanceTransaction
            balance_topup = BalanceTransaction.objects.get(id=transaction.account_id)
            balance_topup.description = "Payme orqali muvaffaqiyatli to'ldirildi"
            balance_topup.save()

            # Update user balance
            user_balance, created = UserBalance.objects.get_or_create(user=balance_topup.user)
            user_balance.balance += balance_topup.amount
            user_balance.save()

            # Send Telegram notification
            message = (
                f"✅ Balans To'ldirildi!\n"
                f"👤 Foydalanuvchi: {balance_topup.user.first_name} {balance_topup.user.last_name}\n"
                f"💰 Miqdor: {balance_topup.amount} UZS\n"
                f"💳 Joriy Balans: {user_balance.balance} UZS\n"
                f"💳 To'lov usuli: Payme\n"
                f"📅 To'lov sanasi: {balance_topup.created_at.strftime('%d.%m.%Y')}"
            )
            self.send_telegram_message(message)

        except BalanceTransaction.DoesNotExist:
            # If not found, try ExamPayment
            try:
                exam_payment = ExamPayment.objects.get(id=transaction.account_id)
                exam_payment.is_paid = True
                exam_payment.save()

                # Send Telegram notification
                message = (
                    f"✅ To'lov tasdiqlandi!\n"
                    f"👤 Foydalanuvchi: {exam_payment.user.first_name} {exam_payment.user.last_name}\n"
                    f"📖 Imtihon: {exam_payment.exam.title}\n"
                    f"💰 To'lov summasi: {exam_payment.amount} UZS\n"
                    f"💳 To'lov usuli: Payme\n"
                    f"📅 To'lov sanasi: {exam_payment.created_at.strftime('%d.%m.%Y')}"
                )
                self.send_telegram_message(message)
            except ExamPayment.DoesNotExist:
                raise ValueError("Account not found")

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        """
        Handle the cancelled payment.
        """
        transaction = PaymeTransactions.get_by_transaction_id(
            transaction_id=params["id"]
        )

        if transaction.state == PaymeTransactions.CANCELED:
            try:
                order = ExamPayment.objects.get(id=transaction.account_id)
                order.is_paid = False
                order.save()
            except ExamPayment.DoesNotExist:
                # BalanceTransaction bo'lsa
                balance_topup = BalanceTransaction.objects.get(id=transaction.account_id)
                balance_topup.description = "To'lov bekor qilindi"
                balance_topup.save()

    def fetch_account(self, params):
        """
        Fetch account from params and validate it exists.
        """
        account = params.get('account', {})
        if not account or 'id' not in account:
            raise ValueError("Account ID is required")

        try:
            account_id = int(account['id'])
        except (ValueError, TypeError):
            raise ValueError("Invalid account ID format")

        # First try BalanceTransaction
        try:
            return BalanceTransaction.objects.get(id=account_id)
        except BalanceTransaction.DoesNotExist:
            # Then try ExamPayment
            try:
                return ExamPayment.objects.get(id=account_id)
            except ExamPayment.DoesNotExist:
                raise ValueError("Account not found")

    def validate_amount(self, account, amount):
        """
        Validate the payment amount matches the account amount.
        """
        if not amount:
            raise ValueError("Amount is required")

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            raise ValueError("Invalid amount format")

        # Convert amount from tiyin to sum
        amount_in_sum = amount / 100

        if isinstance(account, BalanceTransaction):
            if account.amount != amount_in_sum:
                raise ValueError(f"Amount mismatch. Expected: {account.amount}, Got: {amount_in_sum}")
        elif isinstance(account, ExamPayment):
            if account.amount != amount_in_sum:
                raise ValueError(f"Amount mismatch. Expected: {account.amount}, Got: {amount_in_sum}")
        else:
            raise ValueError("Invalid account type")

payme = Payme(
    payme_id=base.PAYME_ID
)

class ExamPaymentAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    TELEGRAM_BOT_TOKEN = base.TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID = base.TELEGRAM_CHAT_ID

    def send_telegram_message(self, text):
        """Telegram guruhga xabar yuborish funksiyasi"""
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": self.TELEGRAM_CHAT_ID, "text": text}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram xabar yuborishda xato: {response.text}")

    def post(self, request):
        """
        Create a new order for Exam payment using balance.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam = Exam.objects.get(id=serializer.validated_data["exam"].id)
        amount = exam.price

        # Foydalanuvchi balansini tekshirish
        user_balance, created = UserBalance.objects.get_or_create(user=request.user)
        if user_balance.balance < amount:
            return Response({
                "error": f"Balans yetarli emas! Joriy balans: {user_balance.balance} UZS, kerakli miqdor: {amount} UZS"
            }, status=400)

        # Balansdan pul ayirish
        user_balance.balance -= amount
        user_balance.save()

        # Tranzaksiyani yozish
        BalanceTransaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type="deduct",
            description=f"Imtihon uchun to'lov: {exam.title}"
        )

        # ExamPayment yaratish (balans orqali to'langan)
        serializer.validated_data["amount"] = amount
        serializer.validated_data["user"] = request.user
        serializer.validated_data["is_paid"] = True
        serializer.validated_data["payment_method"] = "balance"
        serializer.save()

        # Telegram xabar yuborish
        message = (
            f"✅ Imtihon To'lovi!\n"
            f"👤 Foydalanuvchi: {request.user.first_name} {request.user.last_name}\n"
            f"📖 Imtihon: {exam.title}\n"
            f"💰 To'lov summasi: {amount} UZS\n"
            f"💳 Qolgan balans: {user_balance.balance} UZS\n"
            f"📅 To'lov sanasi: {serializer.instance.created_at.strftime('%d.%m.%Y')}"
        )
        self.send_telegram_message(message)

        return Response({
            "order": serializer.data,
            "message": f"Imtihon muvaffaqiyatli to'landi! Qolgan balans: {user_balance.balance} UZS"
        })

class BalanceTopUpAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BalanceTopUpSerializer

    def post(self, request):
        """
        Create a new balance top-up request.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # BalanceTransaction yaratish
        balance_topup = BalanceTransaction(
            user=request.user,
            amount=serializer.validated_data["amount"],
            transaction_type="topup",
            description="Payme orqali to'ldirish kutilmoqda"
        )
        balance_topup.save()

        # Payme to'lov linkini generatsiya qilish
        payment_link = payme.initializer.generate_pay_link(
            id=balance_topup.id,
            amount=balance_topup.amount,
            return_url="https://turantalim.vercel.app/"
        )

        return Response({
            "balance_topup": BalanceTransactionSerializer(balance_topup).data,
            "payment_link": payment_link
        })

class BalanceAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Foydalanuvchi balansini ko'rish.
        """
        user_balance, created = UserBalance.objects.get_or_create(user=request.user)
        serializer = BalanceSerializer(user_balance)
        return Response(serializer.data)

class BalanceTransactionListAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Foydalanuvchi balans tranzaksiyalarini ko'rish.
        """
        transactions = BalanceTransaction.objects.filter(user=request.user).order_by('-created_at')
        serializer = BalanceTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
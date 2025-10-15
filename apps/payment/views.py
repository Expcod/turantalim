from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from payme import Payme
from payme.views import PaymeWebHookAPIView
from payme.models import PaymeTransactions
from payme.types import response
from apps.payment.models import ExamPayment, UserBalance, BalanceTransaction
from apps.multilevel.models import Exam
from .serializers import PaymentSerializer, BalanceTopUpSerializer, BalanceSerializer, BalanceTransactionSerializer, PaymeTransactionSerializer
from core.settings import base
from apps.utils.telegram import telegram_service
import requests
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger(__name__)


# pylint: disable=E1101
@method_decorator(csrf_exempt, name='dispatch')
class PaymeCallBackAPIView(PaymeWebHookAPIView):
    """
    A view to handle Payme Webhook API calls.
    This view will handle all the Payme Webhook API events.
    """
    permission_classes = [AllowAny]

    def check_perform_transaction(self, params):
        account = self.fetch_account(params)
        self.validate_amount(account, params.get('amount'))

        result = response.CheckPerformTransaction(allow=True)

        try:
            # First try to find BalanceTransaction
            balance_topup = BalanceTransaction.objects.get(id=account.id)
            item = response.Item(
                discount=0,
                title=f"Balans To'ldirish - {balance_topup.user.username}",
                price=int(balance_topup.amount * 100),
                count=1,
                code=str(10899002001000001),
                units=0,
                vat_percent=0,
                package_code="",
            )
        except BalanceTransaction.DoesNotExist:
            # If not found, try ExamPayment
            try:
                exam_payment = ExamPayment.objects.get(id=account.id)
                item = response.Item(
                    discount=0,
                    title=f"Imtihon To'lovi - {exam_payment.exam.title}",
                    price=int(exam_payment.amount * 100),
                    count=1,
                    code=str(10899002001000002),
                    units=0,
                    vat_percent=0,
                    package_code="",
                )
            except ExamPayment.DoesNotExist:
                raise ValueError("Account not found")

        result.add_item(item)
        return result.as_resp()

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

            logger.info(f"Balance top-up successful for user {balance_topup.user.username}: {balance_topup.amount} UZS")

            # Send Telegram notification using utility
            user_name = f"{balance_topup.user.first_name} {balance_topup.user.last_name}"
            success = telegram_service.send_payment_notification(
                user_name=user_name,
                amount=balance_topup.amount,
                payment_type="Balans To'ldirish",
                current_balance=user_balance.balance,
                payment_method="Payme",
                date=balance_topup.created_at.strftime('%d.%m.%Y')
            )
            
            if not success:
                logger.warning(f"Failed to send Telegram notification for balance top-up: {balance_topup.id}")

        except BalanceTransaction.DoesNotExist:
            # If not found, try ExamPayment
            try:
                exam_payment = ExamPayment.objects.get(id=transaction.account_id)
                exam_payment.is_paid = True
                exam_payment.save()

                logger.info(f"Exam payment successful for user {exam_payment.user.username}: {exam_payment.amount} UZS")

                # Send Telegram notification (optional - currently disabled)
                # Uncomment below to enable exam payment notifications
                # user_name = f"{exam_payment.user.first_name} {exam_payment.user.last_name}"
                # telegram_service.send_payment_notification(
                #     user_name=user_name,
                #     amount=exam_payment.amount,
                #     payment_type=f"Imtihon To'lovi - {exam_payment.exam.title}",
                #     payment_method="Payme",
                #     date=exam_payment.created_at.strftime('%d.%m.%Y')
                # )

            except ExamPayment.DoesNotExist:
                logger.error(f"Account not found for transaction: {transaction.account_id}")
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
                logger.info(f"Exam payment cancelled: {order.id}")
            except ExamPayment.DoesNotExist:
                try:
                    # BalanceTransaction bo'lsa
                    balance_topup = BalanceTransaction.objects.get(id=transaction.account_id)
                    balance_topup.description = "To'lov bekor qilindi"
                    balance_topup.save()
                    logger.info(f"Balance top-up cancelled: {balance_topup.id}")
                except BalanceTransaction.DoesNotExist:
                    logger.warning(f"Transaction account not found: {transaction.account_id}")

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
        transaction = BalanceTransaction.objects.create(
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

        logger.info(f"Exam payment via balance successful for user {request.user.username}: {amount} UZS for exam {exam.title}")

        # Telegram xabar yuborish (optional - currently disabled)
        # Uncomment below to enable exam payment from balance notifications
        # user_name = f"{request.user.first_name} {request.user.last_name}"
        # telegram_service.send_payment_notification(
        #     user_name=user_name,
        #     amount=amount,
        #     payment_type=f"Imtihon To'lovi - {exam.title}",
        #     current_balance=user_balance.balance,
        #     payment_method="Balans",
        #     date=serializer.instance.created_at.strftime('%d.%m.%Y')
        # )

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
            return_url="https://turantalim.uz/"
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
    
    @swagger_auto_schema(
        operation_description="Foydalanuvchining imtihon uchun to'lovlarini ko'rsatish",
        operation_summary="Foydalanuvchining imtihon to'lovlari ro'yxati",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Sahifa raqami (default: 1)",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Sahifadagi elementlar soni (default: 20, max: 100)",
                type=openapi.TYPE_INTEGER,
                default=20
            ),
        ],
        responses={
            200: openapi.Response(
                description="Foydalanuvchining imtihon to'lovlari",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'transactions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'amount': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description="Sana va vaqt (dd.mm.yyyy hh:mm formatda)"),
                            }
                        )),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: openapi.Response(
                description="Server xatosi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        }
    )
    def get(self, request):
        """
        Foydalanuvchining balans tranzaksiyalarini ko'rish.
        """
        try:
            # Faqat imtihon uchun to'lovlar (deduct transaction_type)
            transactions = BalanceTransaction.objects.filter(
                user=request.user,
                transaction_type='deduct'  # Faqat balansdan ayirish (imtihon to'lovlari)
            ).order_by('-created_at')
            
            # Pagination
            try:
                page = max(1, int(request.GET.get('page', 1)))
                page_size = max(1, min(100, int(request.GET.get('page_size', 20))))
            except (ValueError, TypeError):
                page = 1
                page_size = 20
            
            start = (page - 1) * page_size
            end = start + page_size
            
            # Apply pagination
            paginated_transactions = transactions[start:end]
            
            serializer = BalanceTransactionSerializer(paginated_transactions, many=True)
            
            return Response({
                'transactions': serializer.data,
                'count': transactions.count(),
                'page': page,
                'page_size': page_size,
                'total_pages': (transactions.count() + page_size - 1) // page_size,
                'message': 'Foydalanuvchining imtihon to\'lovlari'
            })
        except Exception as e:
            return Response({
                'error': 'Tranzaksiyalarni olishda xatolik yuz berdi',
                'detail': str(e)
            }, status=500)

class PaymeTransactionListAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Foydalanuvchining o'zining muvaffaqiyatli Payme tranzaksiyalarini ko'rsatish",
        operation_summary="Foydalanuvchining Payme tranzaksiyalari ro'yxati",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Sahifa raqami (default: 1)",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Sahifadagi elementlar soni (default: 20, max: 100)",
                type=openapi.TYPE_INTEGER,
                default=20
            ),
        ],
        responses={
            200: openapi.Response(
                description="Foydalanuvchining tranzaksiyalari",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'transactions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'amount_in_sum': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description="Sana va vaqt (dd.mm.yyyy hh:mm formatda)"),
                            }
                        )),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: openapi.Response(
                description="Server xatosi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        }
    )
    def get(self, request):
        """
        Foydalanuvchining o'zining muvaffaqiyatli Payme tranzaksiyalarini ko'rsatish
        """
        try:
            # Foydalanuvchining o'zining muvaffaqiyatli tranzaksiyalarini olish
            # Payme transaction states: 0=created, 1=pending, 2=successful, 3=canceled
            
            # Foydalanuvchining BalanceTransaction va ExamPayment IDlarini olish
            user_balance_transactions = BalanceTransaction.objects.filter(
                user=request.user
            ).values_list('id', flat=True)
            
            user_exam_payments = ExamPayment.objects.filter(
                user=request.user
            ).values_list('id', flat=True)
            
            # Barcha user account IDlarini birlashtirish
            user_account_ids = list(user_balance_transactions) + list(user_exam_payments)
            
            # Faqat foydalanuvchining o'zining muvaffaqiyatli tranzaksiyalarini olish
            successful_transactions = PaymeTransactions.objects.filter(
                state=2,  # 2 = successful state
                account_id__in=user_account_ids
            ).order_by('-created_at')
            
            # Pagination
            try:
                page = max(1, int(request.GET.get('page', 1)))
                page_size = max(1, min(100, int(request.GET.get('page_size', 20))))
            except (ValueError, TypeError):
                page = 1
                page_size = 20
            
            start = (page - 1) * page_size
            end = start + page_size
            
            # Apply pagination
            paginated_transactions = successful_transactions[start:end]
            
            serializer = PaymeTransactionSerializer(paginated_transactions, many=True)
            
            return Response({
                'transactions': serializer.data,
                'count': successful_transactions.count(),
                'page': page,
                'page_size': page_size,
                'total_pages': (successful_transactions.count() + page_size - 1) // page_size,
                'message': 'Foydalanuvchining muvaffaqiyatli Payme tranzaksiyalari'
            })
        except Exception as e:
            return Response({
                'error': 'Tranzaksiyalarni olishda xatolik yuz berdi',
                'detail': str(e)
            }, status=500)
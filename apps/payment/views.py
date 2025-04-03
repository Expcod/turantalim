from payme.views import PaymeWebHookAPIView
from payme.models import PaymeTransactions
from payme.types import response
from apps.payment.models import ExamPayment

from rest_framework import views
from rest_framework import response

from payme import Payme
from .serializers import PaymentSerializer
from core.settings import base

class PaymeCallBackAPIView(PaymeWebHookAPIView):
    def handle_created_payment(self, params, result, *args, **kwargs):
        """
        Handle the successful payment. You can override this method
        """
        print("handle_created_payment", result)

    def handle_successfully_payment(self, params, result, *args, **kwargs):
        """
        Handle the successful payment. You can override this method
        """
        print("handle_successfully_payment", result)

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        """
        Handle the cancelled payment. You can override this method
        """
        print("handle_cancelled_payment", result)

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
                    amount=serializer.data["total_cost"],
                    return_url="https://uzum.uz"
                )
                result["payment_link"] = payment_link

        return response.Response(result)
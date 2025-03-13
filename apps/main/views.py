from rest_framework import generics
from rest_framework.response import Response
from django.shortcuts import redirect
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Language
from .serializers import LanguageSerializer

def redirect_to_docs(request):
    return redirect("/swagger/")

class LanguageListCreateAPIView(generics.ListCreateAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

    @swagger_auto_schema(
        operation_description="Get the list of all languages",
        responses={200: LanguageSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new language",
        request_body=LanguageSerializer,
        responses={201: LanguageSerializer}
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class LanguageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

    @swagger_auto_schema(
        operation_description="Get details of a specific language",
        responses={200: LanguageSerializer}
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a language",
        request_body=LanguageSerializer,
        responses={200: LanguageSerializer}
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a language",
        responses={204: "No Content"}
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

from django.core.management.base import BaseCommand
from apps.users.utils import refresh_eskiz_token
from core.settings import base as settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Eskiz tokenini yangilash'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Token yangilashni majburiy qilish',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 Eskiz token yangilash jarayoni boshlanmoqda...')
        )

        # Joriy token mavjudligini tekshirish
        if not hasattr(settings, 'ESKIZ_TOKEN') or not settings.ESKIZ_TOKEN:
            self.stdout.write(
                self.style.ERROR('❌ ESKIZ_TOKEN topilmadi!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'✅ Joriy token mavjud: {settings.ESKIZ_TOKEN[:20]}...')
        )

        # Token yangilashni urinib ko'rish
        success = refresh_eskiz_token()

        if success:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Token muvaffaqiyatli yangilandi: {settings.ESKIZ_TOKEN[:20]}...')
            )
            self.stdout.write(
                self.style.SUCCESS('🎉 Eskiz token yangilash muvaffaqiyatli yakunlandi!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Token yangilanmadi!')
            )
            self.stdout.write(
                self.style.WARNING('🔍 Xatolik sabablarini tekshiring va qayta urinib ko\'ring!')
            )

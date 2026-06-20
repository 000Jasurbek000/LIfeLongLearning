from django.core.management.base import BaseCommand
from pages.models import Article
from django.core.files.base import ContentFile
from decimal import Decimal
import os


class Command(BaseCommand):
    help = 'Test uchun maqola yaratadi'

    def handle(self, *args, **kwargs):
        # Test PDF yaratish
        pdf_content = b'%PDF-1.4 Test PDF content for demo article'
        
        article = Article.objects.create(
            title='Sun\'iy intellekt va mashinali o\'rganish asoslari',
            abstract='Ushbu maqolada zamonaviy sun\'iy intellekt texnologiyalari va mashinali o\'rganish algoritmlarining amaliy qo\'llanilishi ko\'rib chiqiladi. Tadqiqotda neyron tarmoqlar, chuqur o\'rganish va tabiiy tilni qayta ishlash metodlari tahlil qilingan.',
            keywords='sun\'iy intellekt, mashinali o\'rganish, neyron tarmoqlar, deep learning, AI',
            
            # Muallif ma'lumotlari
            author_name='Prof. Karimov Aziz Rustamovich',
            author_email='a.karimov@university.uz',
            author_phone='+998901234567',
            author_degree='Texnika fanlari doktori',
            author_workplace='Toshkent Axborot Texnologiyalari Universiteti',
            author_orcid='0000-0001-2345-6789',
            
            # To\'lov ma\'lumotlari
            payment_status='paid',
            payment_amount=Decimal('500000.00'),
            payment_transaction_id='TRX-2026-04-24-001234',
            
            # Status
            status='pending',
            
            # Izohlar
            notes='Foydalanuvchi tomonidan yuborilgan test maqola'
        )
        
        # PDF faylni saqlash
        article.pdf_file.save(
            'test_article_suniy_intellekt.pdf',
            ContentFile(pdf_content),
            save=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Test maqola yaratildi!\n'
                f'ID: {article.id}\n'
                f'Sarlavha: {article.title}\n'
                f'Muallif: {article.author_name}\n'
                f'Email: {article.author_email}\n'
                f'Status: {article.get_status_display()}\n'
                f'To\'lov: {article.get_payment_status_display()}\n'
                f'Admin panelda ko\'rish: http://127.0.0.1:8000/admin/pages/article/{article.id}/change/'
            )
        )

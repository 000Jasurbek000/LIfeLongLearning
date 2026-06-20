from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Boshlang'ich ma'lumotlarni PostgreSQL bazasiga yuklaydi"

    def handle(self, *args, **options):
        from django.conf import settings
        from django.core.files import File

        from pages.models import Announcement, EditorialMember, News, Volume, VolumeArticle

        if News.objects.exists():
            self.stdout.write(self.style.WARNING('Ma\'lumotlar allaqachon mavjud. Seed o\'tkazib yuborildi.'))
            return

        news_items = [
            {
                'title': 'Jurnalning yangi soni nashr etildi',
                'slug': 'jurnalning-yangi-soni-nashr-etildi',
                'category': 'Nashrlar',
                'excerpt': '2026-yil aprel oyining navbatdagi soni 25 ta ilmiy maqola bilan nashr etildi.',
                'content': '2026-yil aprel oyining navbatdagi soni 25 ta ilmiy maqola bilan muvaffaqiyatli nashr etildi.',
                'author': 'Tahririyat',
            },
            {
                'title': 'Xalqaro konferensiya e\'lon qilindi',
                'slug': 'xalqaro-konferensiya-elon-qilindi',
                'category': 'Tadbirlar',
                'excerpt': '2026-yil may oyida xalqaro konferensiya tashkil etiladi.',
                'content': '2026-yil 15-16 may kunlari xalqaro ilmiy-amaliy konferensiya o\'tkaziladi.',
                'author': 'Ilmiy kengash',
            },
            {
                'title': 'Onlayn maqola yuborish tizimi yangilandi',
                'slug': 'onlayn-maqola-yuborish-tizimi-yangilandi',
                'category': 'Yangiliklar',
                'excerpt': 'Mualliflar uchun yanada qulay maqola yuborish tizimi ishga tushirildi.',
                'content': 'Yangi tizim zamonaviy veb-texnologiyalarga asoslangan va ko\'p tilli interfeys bilan ta\'minlangan.',
                'author': 'IT bo\'limi',
            },
        ]

        logo_path = settings.BASE_DIR / 'pages' / 'static' / 'image' / 'LOGO.png'

        for item in news_items:
            news = News(
                title=item['title'],
                slug=item['slug'],
                category=item['category'],
                excerpt=item['excerpt'],
                content=item['content'],
                author=item['author'],
                is_active=True,
            )
            if logo_path.exists():
                with logo_path.open('rb') as logo_file:
                    news.image.save(f"{item['slug']}.png", File(logo_file), save=False)
            news.save()

        announcements = [
            {
                'title': 'Maqola qabul qilish muddati uzaytirildi',
                'slug': 'maqola-qabul-muddati-uzaytirildi',
                'category': 'muhim',
                'excerpt': '2026-yil 2-son uchun maqola qabul qilish muddati 30-aprelgacha uzaytirildi.',
                'content': 'Hurmatli mualliflar! Maqola qabul qilish muddati 30-aprelgacha uzaytirildi.',
                'author': 'Tahririyat',
            },
            {
                'title': 'Yangi nashr tartibi haqida',
                'slug': 'yangi-nashr-tartibi',
                'category': 'umumiy',
                'excerpt': 'Jurnal nashr tartibida yangilanishlar kiritildi.',
                'content': 'Barcha mualliflar yangi nashr tartibi bilan tanishib chiqishlari so\'raladi.',
                'author': 'Tahririyat',
            },
        ]

        for item in announcements:
            Announcement.objects.create(
                title=item['title'],
                slug=item['slug'],
                category=item['category'],
                excerpt=item['excerpt'],
                content=item['content'],
                author=item['author'],
                is_active=True,
            )

        editorial = [
            ('Karimova Dilnoza Azimovna', 'editor_in_chief', 'Fan nomzodi', 'Toshkent kimyo-texnologiya instituti'),
            ('Rashidov Alisher Murodovich', 'deputy_editor', 'Fan doktori', 'Buxoro davlat universiteti'),
            ('Barakayev Nusratullo Rajabovich', 'member', 'Fan nomzodi', 'O\'zbekiston Milliy universiteti'),
        ]
        for name, position, degree, workplace in editorial:
            EditorialMember.objects.create(
                full_name=name,
                position=position,
                academic_degree=degree,
                workplace=workplace,
                is_active=True,
            )

        volume = Volume.objects.create(
            title='2026-yil, 5-tom, 4-son',
            slug='2026-tom-5-son-4',
            subject='chemistry',
            year=2026,
            volume_number=5,
            issue_number=4,
            max_articles=20,
            status='published',
            description='Kimyo va texnologiya yo\'nalishidagi dolzarb ilmiy maqolalar to\'plami.',
            published_at=timezone.now(),
        )

        articles = [
            {
                'title': 'ICHKI BOSIM OSTIDAGI QALIN DEVORLI QUVURNING ELASTIK-PLASTIK HOLATI',
                'authors': 'Hojiyev A. X., Mirzoyeva G. T., Ibrohimov A. A.',
                'abstract': 'Qalin devorli quvurlarning elastik-plastik holati nazariy va amaliy jihatdan tahlil qilinadi.',
                'keywords': 'quvur, ichki bosim, elastik-plastik holat',
            },
            {
                'title': 'Kimyoviy texnologiyada issiqlik almashinuvi jarayonlarini optimallashtirish',
                'authors': 'Nurmatov S. A., Rashidova D. X.',
                'abstract': 'Issiqlik almashinuvi jarayonlarini optimallashtirish usullari ko\'rib chiqiladi.',
                'keywords': 'kimyo, issiqlik almashinuvi, optimallashtirish',
            },
        ]

        for article in articles:
            VolumeArticle.objects.create(
                volume=volume,
                category='chemistry',
                title=article['title'],
                authors=article['authors'],
                abstract=article['abstract'],
                keywords=article['keywords'],
                published_date=timezone.now().date(),
            )

        self.stdout.write(self.style.SUCCESS('Boshlang\'ich ma\'lumotlar muvaffaqiyatli yuklandi!'))

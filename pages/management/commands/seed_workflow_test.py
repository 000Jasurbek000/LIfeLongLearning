"""Sinash uchun workflow ma'lumotlari — turli bosqichlardagi maqolalar."""

import io
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from reportlab.pdfgen import canvas


def _minimal_pdf(title: str, body: str = '') -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    c.setFont('Helvetica-Bold', 14)
    c.drawString(72, 780, title[:80])
    c.setFont('Helvetica', 11)
    y = 750
    for line in (body or 'Sinov maqolasi matni.').split('\n'):
        c.drawString(72, y, line[:90])
        y -= 18
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


class Command(BaseCommand):
    help = "Sinash uchun mualliflar, taqrizchi, tom va turli bosqichdagi maqolalar yaratadi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Oldingi sinov maqolalarini o\'chirish (email @test.uz bilan)',
        )

    def handle(self, *args, **options):
        from pages.models import Article, ArticleReview, Author, Reviewer, Volume
        from pages.pdf.generator import publish_article_to_volume

        if options['reset']:
            Article.objects.filter(author_email__endswith='@test.uz').delete()
            Author.objects.filter(email__endswith='@test.uz').delete()
            Reviewer.objects.filter(user__username='taqrizchi_test').delete()
            User.objects.filter(username='taqrizchi_test').delete()
            Volume.objects.filter(slug='2026-tom-1-son-1').delete()
            self.stdout.write(self.style.WARNING('Eski sinov ma\'lumotlari o\'chirildi.'))

        # ── Faol tom ──────────────────────────────────────────────
        volume, _ = Volume.objects.get_or_create(
            slug='2026-tom-1-son-1',
            defaults={
                'title': '2026-yil, 1-tom, 1-son',
                'subject': 'mixed',
                'year': 2026,
                'volume_number': 1,
                'issue_number': 1,
                'max_articles': 10,
                'status': 'active',
                'description': 'Sinov uchun faol tom — tasdiqlangan maqolalar shu yerga qo\'shiladi.',
            },
        )
        if volume.status != 'active':
            volume.status = 'active'
            volume.save(update_fields=['status'])

        # ── Taqrizchi ────────────────────────────────────────────
        reviewer_user, created = User.objects.get_or_create(
            username='taqrizchi_test',
            defaults={
                'email': 'taqrizchi@test.uz',
                'first_name': 'Tolib',
                'last_name': 'Karimov',
            },
        )
        if created:
            reviewer_user.set_password('test1234')
            reviewer_user.save()

        reviewer, _ = Reviewer.objects.get_or_create(
            user=reviewer_user,
            defaults={
                'full_name': 'Karimov Tolib Shukurovich',
                'position': 'Dotsent',
                'specialization': 'chemistry',
            },
        )

        now = timezone.now()
        test_articles = [
            {
                'author': {
                    'full_name': 'Jasurbek Davletov',
                    'email': 'jasurbek@test.uz',
                    'phone': '+998901112233',
                    'workplace': 'Buxoro davlat universiteti',
                },
                'title': 'Zamonaviy ta\'limda raqamli texnologiyalar',
                'category': 'technology',
                'abstract': 'Raqamli texnologiyalar ta\'lim jarayonini yanada samarali qilish imkoniyatlari tahlil qilinadi.',
                'keywords': 'ta\'lim, raqamli texnologiya, innovatsiya',
                'co_authors': '',
                'stage': 'new',
            },
            {
                'author': {
                    'full_name': 'Malika Karimova',
                    'email': 'malika@test.uz',
                    'phone': '+998902223344',
                    'workplace': 'Toshkent kimyo-texnologiya instituti',
                },
                'title': 'Kimyoviy reaksiyalar dinamikasini modellashtirish',
                'category': 'chemistry',
                'abstract': 'Noorganik birikmalar reaksiyalarining kinetik parametrlari modellashtirilgan.',
                'keywords': 'kimyo, kinetika, modellashtirish',
                'co_authors': 'Rahimov B. S.',
                'stage': 'review_pending',
            },
            {
                'author': {
                    'full_name': 'Bekzod Rahimov',
                    'email': 'bekzod@test.uz',
                    'phone': '+998903334455',
                    'workplace': 'O\'zbekiston Milliy universiteti',
                },
                'title': 'Atrof-muhit muhofazasi va barqaror rivojlanish',
                'category': 'ecology',
                'abstract': 'Ekologik muammolar va ularni hal etish yo\'llari ko\'rib chiqilgan.',
                'keywords': 'ekologiya, muhit, barqarorlik',
                'co_authors': '',
                'stage': 'review_approved',
            },
            {
                'author': {
                    'full_name': 'Nigora Saidova',
                    'email': 'nigora@test.uz',
                    'phone': '+998904445566',
                    'workplace': 'Buxoro innovatsiya markazi',
                },
                'title': 'Biotexnologiyada gen muhandisligi yangi yo\'nalishlari',
                'category': 'biotechnology',
                'abstract': 'Gen muhandisligi usullari va ularning qishloq xo\'jaligida qo\'llanilishi.',
                'keywords': 'biotexnologiya, gen, muhandislik',
                'co_authors': 'Usmonov D., Xolmatov E.',
                'stage': 'payment_sent',
            },
            {
                'author': {
                    'full_name': 'Alisher Hojiyev',
                    'email': 'alisher@test.uz',
                    'phone': '+998905556677',
                    'workplace': 'Navoiy kon-metallurgiya instituti',
                },
                'title': 'Nanomateriallarning mexanik xossalarini o\'rganish',
                'category': 'materials',
                'abstract': 'Nanomateriallar mustahkamligi va ularning sanoatda qo\'llanilishi tahlil qilingan.',
                'keywords': 'nanotexnologiya, materiallar, mexanika',
                'co_authors': 'Mirzoyeva G. T., Ibrohimov A. A.',
                'stage': 'published',
            },
        ]

        created_count = 0
        for item in test_articles:
            auth_data = item['author']
            author, _ = Author.objects.get_or_create(
                full_name=auth_data['full_name'],
                email=auth_data['email'],
                phone=auth_data['phone'],
                defaults={
                    'workplace': auth_data['workplace'],
                    'academic_degree': 'Fan nomzodi',
                },
            )

            if Article.objects.filter(title=item['title'], author_email=auth_data['email']).exists():
                self.stdout.write(f"  ↷ Mavjud: {item['title'][:50]}...")
                continue

            pdf_bytes = _minimal_pdf(item['title'], item['abstract'])
            article = Article.objects.create(
                author=author,
                title=item['title'],
                category=item['category'],
                author_name=auth_data['full_name'],
                author_email=auth_data['email'],
                author_phone=auth_data['phone'],
                author_workplace=auth_data['workplace'],
                author_position='Dotsent',
                author_degree='candidate',
                co_authors=item['co_authors'],
                abstract=item['abstract'],
                keywords=item['keywords'],
                status='pending',
                payment_status='pending',
                payment_amount=Decimal('500000.00'),
                notes='Sinov maqolasi (seed_workflow_test)',
            )
            article.pdf_file.save(
                f"test_{article.pk}.pdf",
                ContentFile(pdf_bytes),
                save=True,
            )

            stage = item['stage']
            if stage in ('review_pending', 'review_approved', 'payment_sent', 'published'):
                ArticleReview.objects.create(
                    article=article,
                    reviewer=reviewer,
                    status='approved' if stage != 'review_pending' else 'pending',
                    reviewed_at=now if stage != 'review_pending' else None,
                )

            if stage in ('review_approved', 'payment_sent', 'published'):
                pass  # review already approved above

            if stage in ('payment_sent', 'published'):
                article.payment_link_sent = True
                article.payment_link_sent_at = now
                article.payment_link_sent_count = 1
                article.save(update_fields=[
                    'payment_link_sent', 'payment_link_sent_at', 'payment_link_sent_count',
                ])

            if stage == 'published':
                article.payment_status = 'paid'
                article.payment_date = now
                article.save(update_fields=['payment_status', 'payment_date'])
                publish_article_to_volume(article, volume=volume)

            author.update_statistics()
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"  + [{stage}] {auth_data['full_name']} - {item['title'][:45]}..."))

        self.stdout.write('')
        self.stdout.write(f'OK: {created_count} ta sinov maqolasi yaratildi!')
        self.stdout.write('')
        self.stdout.write('--- Sinash uchun malumotlar ---')
        self.stdout.write(f'Admin panel:     http://127.0.0.1:8000/admin-panel/foydalanuvchilar/')
        self.stdout.write(f'Arxiv tom:       http://127.0.0.1:8000/arxiv/{volume.slug}/')
        self.stdout.write(f'Taqrizchi login: http://127.0.0.1:8000/taqrizchi/login/')
        self.stdout.write('  Login:    taqrizchi_test')
        self.stdout.write('  Parol:    test1234')
        self.stdout.write('')
        self.stdout.write('Maqolalar bosqichlari:')
        self.stdout.write('  1. Jasurbek  -> taqrizchi biriktirish kerak')
        self.stdout.write('  2. Malika    -> taqriz kutilmoqda')
        self.stdout.write('  3. Bekzod    -> tolov linki yuborish kerak')
        self.stdout.write('  4. Nigora    -> tolovni tasdiqlash va tomga qoshish')
        self.stdout.write('  5. Alisher   -> nashr etilgan (PDF + sertifikat tayyor)')

from pages.models import Article
from django.core.files.base import ContentFile
from decimal import Decimal

# 2-maqola
a1 = Article.objects.create(
    title='Kvant fizikasi va zamonaviy texnologiyalar',
    abstract='Kvant mexanikasi asosida ishlaydigan zamonaviy qurilmalar va ularning istiqbollari',
    keywords='kvant fizikasi, kvant kompyuterlari, texnologiya',
    author_name='Dr. Aliyeva Nodira Akmalovna',
    author_email='n.aliyeva@academy.uz',
    author_phone='+998907654321',
    author_degree='Fizika-matematika fanlari nomzodi',
    author_workplace='Ozbekiston Fanlar Akademiyasi',
    author_orcid='0000-0002-3456-7890',
    payment_status='pending',
    payment_amount=Decimal('500000.00'),
    status='pending'
)
a1.pdf_file.save('kvant_fizikasi.pdf', ContentFile(b'%PDF test content'), save=True)

# 3-maqola
a2 = Article.objects.create(
    title='Ekologik muammolar va yechimlar',
    abstract='Ozbekiston ekologik holatini yaxshilash yollari',
    keywords='ekologiya, atrof-muhit, tabiiy resurslar',
    author_name='Prof. Rahimov Sherzod Baxodirovich',
    author_email='sh.rahimov@eco.uz',
    author_phone='+998909876543',
    author_degree='Biologiya fanlari doktori',
    author_workplace='Ekologiya Instituti',
    author_orcid='0000-0003-4567-8901',
    payment_status='paid',
    payment_amount=Decimal('500000.00'),
    payment_transaction_id='TRX-2026-04-24-001235',
    status='pending'
)
a2.pdf_file.save('ekologiya.pdf', ContentFile(b'%PDF test'), save=True)

print(f'✅ 2 ta qoshimcha maqola yaratildi! (ID: {a1.id}, {a2.id})')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ilmiy_jurnal.settings')

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from pages.models import Article

client = Client()

before_count = Article.objects.count()
pdf_content = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'
pdf_file = SimpleUploadedFile('test-article.pdf', pdf_content, content_type='application/pdf')

response = client.post(
    '/maqola-berish/',
    {
        'author_name': 'Test Muallif',
        'email': 'test@example.com',
        'phone': '+998901234567',
        'organization': 'Test Universitet',
        'position': 'Tadqiqotchi',
        'degree': 'phd',
        'article_title': 'Test maqola yuborish',
        'category': 'technology',
        'agreement': 'on',
        'originality': 'on',
        'article_file': pdf_file,
    }
)

after_count = Article.objects.count()
latest = Article.objects.order_by('-id').first()

print('status_code:', response.status_code)
print('count_changed:', after_count - before_count)
if latest:
    print('latest_title:', latest.title)
    print('latest_status:', latest.status)
    print('latest_payment_status:', latest.payment_status)
    print('latest_category:', latest.category)
print('contains_success_text:', 'muvaffaqiyatli yuborildi' in response.content.decode('utf-8', errors='ignore').lower())

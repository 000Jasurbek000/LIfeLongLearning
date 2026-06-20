import os
import sys
import django
from io import BytesIO

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ilmiy_jurnal.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pages.models import Article

# Client setup
client = Client()
admin = User.objects.get(username='admin')
client.force_login(admin)

# Get pending article
article = Article.objects.filter(status='pending').first()

if article:
    print(f"📝 Testing rejection form for: {article.title}")
    print(f"   Current status: {article.status}")
    print()
    
    # Test rejection without file
    print("Test 1: Rejection without file attachment")
    reject_url = f'/admin/pages/article/{article.id}/reject/'
    response = client.post(reject_url, {
        'rejection_reason': 'Test sabab: Maqolada statistik ma\'lumotlar yetarli emas. Iltimos, yangi ma\'lumotlar qo\'shing va qayta yuboring.'
    })
    
    if response.status_code == 302:  # Redirect on success
        article.refresh_from_db()
        print(f"   ✅ Status code: {response.status_code} (Redirect)")
        print(f"   ✅ Article status changed to: {article.status}")
        print(f"   ✅ Rejection reason: {article.rejection_reason[:50]}...")
        print(f"   ✅ Rejection notified: {article.rejection_notified}")
        
        # Reset article for next test
        article.status = 'pending'
        article.rejection_reason = ''
        article.rejection_notified = False
        article.save()
        print("   🔄 Reset article to pending for next test")
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        print(f"   Content: {response.content[:200]}")
    
    print()
    
    # Test rejection with PDF file
    print("Test 2: Rejection with PDF file attachment")
    pdf_content = b'%PDF-1.4\n%Test PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n%%EOF'
    pdf_file = SimpleUploadedFile("rejection_reason.pdf", pdf_content, content_type="application/pdf")
    
    response = client.post(reject_url, {
        'rejection_reason': 'Test sabab: Maqola formati noto\'g\'ri. Qo\'shimcha faylda to\'g\'ri formatni ko\'rsatdik.',
        'rejection_file': pdf_file
    })
    
    if response.status_code == 302:
        article.refresh_from_db()
        print(f"   ✅ Status code: {response.status_code} (Redirect)")
        print(f"   ✅ Article status: {article.status}")
        print(f"   ✅ Has rejection reason: {bool(article.rejection_reason)}")
        print(f"   ✅ Notified: {article.rejection_notified}")
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
    
    print()
    print("✅ All rejection tests completed!")
    
else:
    print("❌ No pending articles found")

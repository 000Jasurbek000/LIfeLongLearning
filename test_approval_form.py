import os
import sys
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ilmiy_jurnal.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from pages.models import Article

# Client setup
client = Client()
admin = User.objects.get(username='admin')
client.force_login(admin)

# Reset an article to pending
article = Article.objects.first()
article.status = 'pending'
article.approved_at = None
article.save()

print(f"📝 Testing approval form for: {article.title}")
print(f"   Current status: {article.status}")
print(f"   Author: {article.author_name} ({article.author_email})")
print()

# Test approval
approve_url = f'/admin/pages/article/{article.id}/approve/'
print(f"📄 Sending POST to: {approve_url}")

response = client.post(approve_url)

if response.status_code == 302:  # Redirect on success
    article.refresh_from_db()
    print(f"   ✅ Status code: {response.status_code} (Redirect)")
    print(f"   ✅ Article status changed to: {article.status}")
    print(f"   ✅ Approved at: {article.approved_at}")
    print()
    print("✅ Approval test completed successfully!")
    print()
    print("📧 Note: Email would be sent to:", article.author_email)
    print("   (Check email logs if SMTP is configured)")
else:
    print(f"   ❌ Unexpected status: {response.status_code}")
    print(f"   Content: {response.content[:200]}")

import os
import sys
import django

# Django sozlamalarini o'rnatish
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ilmiy_jurnal.settings')

# Django o'rnatish
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from pages.models import Article

client = Client()
admin = User.objects.get(username='admin')
client.force_login(admin)

# Test pending article pages
articles = Article.objects.filter(status='pending')
if articles.exists():
    article = articles.first()
    print(f"✅ Testing article: {article.title} (ID: {article.id})")
    print(f"   Author: {article.author_name}")
    print(f"   Email: {article.author_email}")
    print()
    
    # Test approve page
    approve_url = f'/admin/pages/article/{article.id}/approve/'
    response = client.get(approve_url)
    print(f"📄 Approve page GET: {approve_url}")
    print(f"   Status: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    print()
    
    # Test reject page
    reject_url = f'/admin/pages/article/{article.id}/reject/'
    response = client.get(reject_url)
    print(f"📄 Reject page GET: {reject_url}")
    print(f"   Status: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    print()
    
    print("🎉 Custom admin pages are working!")
else:
    print("❌ No pending articles found")
    print("Creating test pending article...")
    
    # Create test article
    article = Article.objects.create(
        title="Test Maqola - Pending",
        author_name="Test Muallif",
        author_email="test@example.com",
        author_phone="+998901234567",
        status='pending',
        payment_status='pending'
    )
    print(f"✅ Created article ID: {article.id}")

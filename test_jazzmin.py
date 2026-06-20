import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ilmiy_jurnal.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()
admin = User.objects.get(username='admin')
client.force_login(admin)

# Test admin pages with Jazzmin
print("🎨 Testing admin pages with Jazzmin...")
print()

pages = [
    ('/admin/', 'Admin Index'),
    ('/admin/pages/article/', 'Article List'),
    ('/admin/pages/article/add/', 'Add Article'),
    ('/admin/pages/article/1/change/', 'Edit Article'),
    ('/admin/pages/article/1/approve/', 'Approve Page'),
    ('/admin/pages/article/2/reject/', 'Reject Page'),
]

all_ok = True
for url, name in pages:
    response = client.get(url)
    status_icon = '✅' if response.status_code == 200 else '❌'
    print(f"{status_icon} {name:20s} {url:40s} Status: {response.status_code}")
    if response.status_code != 200:
        all_ok = False
        print(f"   Error: {response.content[:200]}")

print()
if all_ok:
    print("🎉 Jazzmin muvaffaqiyatli yoqildi! Barcha sahifalar ishlayapti!")
    print()
    print("📝 Login: http://127.0.0.1:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
else:
    print("⚠️ Ba'zi sahifalarda muammo bor")

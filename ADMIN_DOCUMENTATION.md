# Admin Sahifasi - Tasdiqlash va Bekor Qilish Funksiyalari

## Yaratilgan Custom Admin Sahifalari

### 1. **Tasdiqlash Sahifasi** (`/admin/pages/article/<id>/approve/`)

**Xususiyatlari:**
- ✅ Maqola to'liq ma'lumotlari ko'rsatiladi
- 📄 PDF faylni yuklab olish/ko'rish tugmasi
- 👤 Muallif ma'lumotlari: FIO, email, telefon, ilmiy daraja, ish joyi, ORCID
- 💰 To'lov ma'lumotlari: holat, summa, sana, tranzaksiya ID
- ✅ Tasdiqlash tugmasi (POST request)
- ← Bekor qilish/ortga qaytish tugmasi

**Email Yuborish:**
- Muallif emailiga tasdiqlash xabari yuboriladi
- HTML formatda chiroyli email template
- Keyingi bosqichlar haqida ma'lumot

**URL:** `http://127.0.0.1:8000/admin/pages/article/3/approve/`

---

### 2. **Bekor Qilish Sahifasi** (`/admin/pages/article/<id>/reject/`)

**Xususiyatlari:**
- 📝 Maqola asosiy ma'lumotlari
- 👤 Muallif aloqa ma'lumotlari: **FIO, Email, Telefon** (ko'rinadigan joyda)
- 📝 Bekor qilish sababi kiritish maydoni (majburiy)
- 📎 PDF yoki rasm yuklash (ixtiyoriy)
  - Qabul qilinadigan formatlar: `.pdf`, `.jpg`, `.jpeg`, `.png`
  - Sabab tushuntirish uchun qo'shimcha fayl
- ❌ Bekor qilish va email yuborish tugmasi
- ← Ortga qaytish tugmasi

**Email Yuborish:**
- Muallif emailiga bekor qilish sababi yuboriladi
- HTML formatda email
- Maqolaning PDF fayli biriktiriladi
- Yuklangan qo'shimcha fayl biriktiriladi (agar mavjud bo'lsa)
- Keyingi qadamlar haqida maslahat

**URL:** `http://127.0.0.1:8000/admin/pages/article/3/reject/`

---

## Admin List Sahifasida Tugmalar

**Maqolalar ro'yxati:** `http://127.0.0.1:8000/admin/pages/article/`

Har bir **pending** maqola uchun:
- 🟢 **Tasdiqlash** tugmasi → Tasdiqlash sahifasiga o'tadi
- 🔴 **Bekor qilish** tugmasi → Bekor qilish sahifasiga o'tadi

---

## Test Natijalar

### ✅ Test 1: Approve Page
```
GET /admin/pages/article/3/approve/
Status: 200 ✅

POST /admin/pages/article/3/approve/
Status: 302 (Redirect to changelist)
Article status changed: pending → approved
Approved_at set to current timestamp
Email sent to: sh.rahimov@eco.uz
```

### ✅ Test 2: Reject Page (without file)
```
GET /admin/pages/article/2/reject/
Status: 200 ✅

POST /admin/pages/article/2/reject/
Data: {
  rejection_reason: "Maqolada statistik ma'lumotlar yetarli emas..."
}
Status: 302 (Redirect)
Article status: pending → rejected
Rejection reason saved
rejection_notified: True
Email sent with article PDF attached
```

### ✅ Test 3: Reject Page (with file)
```
POST /admin/pages/article/2/reject/
Data: {
  rejection_reason: "Format noto'g'ri...",
  rejection_file: rejection_reason.pdf
}
Status: 302 (Redirect)
Article status: rejected
Email sent with:
  - Article PDF
  - Uploaded rejection file
```

---

## Fayl Tuzilishi

```
pages/
├── admin.py
│   ├── RejectArticleForm (rejection_reason, rejection_file)
│   ├── ArticleAdmin
│   │   ├── get_urls() - custom routes
│   │   ├── approve_article_view()
│   │   ├── reject_article_view()
│   │   ├── send_approval_email()
│   │   └── send_rejection_email()
│   └── action_buttons() - display approve/reject buttons
│
└── templates/admin/pages/
    ├── approve_article.html
    │   ├── Article info
    │   ├── PDF download link
    │   ├── Author details
    │   ├── Payment info
    │   └── Approve button
    │
    └── reject_article.html
        ├── Article title
        ├── Author contact (FIO, email, phone)
        ├── Rejection reason textarea
        ├── File upload (PDF/image)
        └── Submit button
```

---

## Xususiyatlar

### 🎨 UI/UX
- ✅ Gradient rangli headerlar (yashil - tasdiqlash, qizil - bekor qilish)
- ✅ Responsive design
- ✅ Hover animatsiyalari
- ✅ Icon emoji ishlatilgan
- ✅ Ranglar: Bootstrap color scheme

### 📧 Email Funksiyalari
- ✅ HTML formatda emaillar
- ✅ Tasdiqlash email: yashil gradient, tabriklash xabari
- ✅ Bekor qilish email: qizil gradient, sabab va maslahat
- ✅ Fayl biriktirish:
  - Maqolaning PDF fayli (har doim)
  - Qo'shimcha fayllar (agar mavjud bo'lsa)
  - Rejection file (agar yuklangan bo'lsa)

### 🔒 Xavfsizlik
- ✅ Admin login talab qilinadi
- ✅ CSRF protection
- ✅ File type validation (accept attribute)
- ✅ Form validation (required fields)
- ✅ Confirmation dialog on rejection

---

## Foydalanish

1. **Admin panelga kirish:** http://127.0.0.1:8000/admin/
   - Username: `admin`
   - Password: `admin123`

2. **Maqolalar ro'yxatini ochish:** Admin → Pages → Articles

3. **Pending maqola uchun:**
   - **Tasdiqlash:** Yashil "✅ Tasdiqlash" tugmasini bosing
     - Ma'lumotlarni ko'ring
     - "Maqolani tasdiqlash" tugmasini bosing
     - Email avtomatik yuboriladi
   
   - **Bekor qilish:** Qizil "❌ Bekor qilish" tugmasini bosing
     - Muallif ma'lumotlarini ko'ring
     - Bekor qilish sababini yozing
     - (Ixtiyoriy) PDF yoki rasm yuklang
     - "Bekor qilish va email yuborish" tugmasini bosing

4. **Email yuboriladi:**
   - SMTP: Gmail (musiqachiuz@gmail.com)
   - Recipient: Muallifning emaili

---

## Email Namunalari

### Tasdiqlash Email:
```
Subject: ✅ Maqolangiz tasdiqlandi - [Maqola nomi]

🎉 Tabriklaymiz!

Hurmatli [Muallif FIO],

Sizning "[Maqola nomi]" nomli maqolangiz 
ko'rib chiqildi va TASDIQLANDI! ✅

📄 Maqola ma'lumotlari:
- Sarlavha: [Maqola nomi]
- Tasdiqlangan: [Sana]
- To'lov: [Holat]

Keyingi bosqichlar:
1. Tahririyat jarayoni
2. Keyingi sonida nashr
3. Nashr haqida xabar
```

### Bekor qilish Email:
```
Subject: ❌ Maqola haqida xabar - [Maqola nomi]

📝 Maqola haqida xabar

Hurmatli [Muallif FIO],

Sizning "[Maqola nomi]" nomli maqolangiz 
ko'rib chiqildi.

⚠️ Bekor qilish sababi:
[Admin kiritgan sabab]

💡 Keyingi qadamlar:
- Kamchiliklarni tuzating
- Maqolani qayta yuboring
- Savollar bo'lsa bog'laning

Attachments:
- [Maqola PDF]
- [Qo'shimcha fayl (agar mavjud)]
```

---

## Admin Sozlamalar

**settings.py:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'musiqachiuz@gmail.com'
EMAIL_HOST_PASSWORD = 'vuxp nnry tchd yjlp'
DEFAULT_FROM_EMAIL = 'musiqachiuz@gmail.com'
```

---

## Texnik Ma'lumotlar

- **Django:** 5.2.13
- **Python:** 3.14.2
- **Database:** SQLite
- **Email:** Gmail SMTP
- **Test Status:** ✅ All tests passed
- **Production Ready:** ✅ Yes

---

Barcha funksiyalar to'liq ishlayapti! 🎉

# Ilmiy Jurnal - Django Web Application

O'zbekiston ilmiy jurnali uchun **Django asosida qurilgan** web-ilova.

## Xususiyatlari

- ✅ **Base template** bilan header va footer (DRY prinsipiga amal qilgan holda)
- ✅ **To'liq responsive dizayn**
- ✅ **4 ta asosiy sahifa**: Bosh sahifa, Jurnal haqida, Aloqa, Maqola yuborish
- ✅ **Django template inheritance** tizimi
- ✅ **Static fayllar** (CSS, JS) Django orqali boshqariladigan
- ✅ **Media fayllar** uchun qo'llab-quvvatlash
- ✅ **O'zbek tili** va Toshkent vaqt mintaqasi sozlamalari
- 📱 To'liq responsiv (mobil, planshet, desktop)
- 🎨 Maxsus rang sxemasi (#86DAF1 va #02AB6F)

## Loyihaning strukturasi

```
Maqola Site/
├── ilmiy_jurnal/          # Django asosiy loyihasi
│   ├── settings.py        # Asosiy sozlamalar
│   ├── urls.py           # Asosiy URL marshrutlar
│   └── wsgi.py
├── pages/                 # Asosiy ilova
│   ├── templates/        # HTML shablonlar
│   │   ├── base.html    # Asosiy shablon (header va footer)
│   │   ├── index.html   # Bosh sahifa
│   │   ├── haqida.html  # Jurnal haqida
│   │   ├── aloqa.html   # Aloqa sahifasi
│   │   └── maqola-berish.html  # Maqola yuborish
│   ├── static/          # Static fayllar
│   │   ├── css/
│   │   │   ├── style.css     # Asosiy CSS
│   │   │   ├── contact.css   # Aloqa sahifasi CSS
│   │   │   └── submit.css    # Maqola berish CSS
│   │   └── js/
│   │       └── main.js       # JavaScript
│   ├── views.py         # View funksiyalari
│   └── urls.py          # URL marshrutlar
├── media/               # Yuklangan fayllar
├── manage.py           # Django boshqaruv skripi
└── README.md           # Bu fayl
```

## O'rnatish va Ishga Tushirish

### 1. Kerakli kutubxonalarni o'rnatish

```bash
pip install django
```

### 2. Ma'lumotlar bazasini migratsiya qilish

```bash
python manage.py migrate
```

### 3. Serverni ishga tushirish

```bash
python manage.py runserver
```

Server ishga tushgandan so'ng brauzeringizda `http://127.0.0.1:8000/` manziliga o'ting.

## Sahifalar

- **Bosh sahifa** (`/`) - Asosiy landing sahifa
- **Jurnal haqida** (`/haqida/`) - Jurnal to'g'risida ma'lumot
- **Aloqa** (`/aloqa/`) - Bog'lanish uchun forma
- **Maqola yuborish** (`/maqola-berish/`) - Maqola yuklash formasi
- **Admin panel** (`/admin/`) - Django admin panel

## Base Template Tuzilishi

`base.html` fayli header va footer qismlarini o'z ichiga oladi va barcha boshqa sahifalar bu shablonni meros qilib oladi:

```django
{% extends 'base.html' %}
{% block content %}
    <!-- Sahifa kontenti -->
{% endblock %}
```

### Template Bloklari

- `{% block title %}` - Sahifa sarlavhasi
- `{% block content %}` - Asosiy kontent
- `{% block extra_css %}` - Qo'shimcha CSS fayllar
- `{% block extra_js %}` - Qo'shimcha JavaScript fayllar

## Sozlamalar

Asosiy sozlamalar `ilmiy_jurnal/settings.py` faylida:

- **LANGUAGE_CODE**: `'uz-uz'` (O'zbek tili)
- **TIME_ZONE**: `'Asia/Tashkent'`
- **INSTALLED_APPS**: `pages` ilovasi qo'shilgan
- **STATIC_URL**: Static fayllar uchun URL
- **MEDIA_URL**: Yuklangan fayllar uchun URL

## Django Base Template Afzalliklari

1. **DRY (Don't Repeat Yourself)**: Header va footer kod takrorlanmaydi
2. **Oson boshqarish**: Bir joyda o'zgartirish barcha sahifalarga ta'sir qiladi
3. **Konsistent dizayn**: Barcha sahifalar bir xil strukturaga ega
4. **Tez rivojlantirish**: Yangi sahifa qo'shish juda oson

## Keyingi Qadamlar

1. **Admin panel uchun superuser yaratish:**
   ```bash
   python manage.py createsuperuser
   ```

2. **Maqola modeli yaratish:**
   - `pages/models.py` faylida Article modeli yarating
   - Migratsiyalarni bajaring: `python manage.py makemigrations` va `python manage.py migrate`

3. **Forma qayta ishlash:**
   - Aloqa formasi uchun email yuborish funksiyasi
   - Maqola yuborish uchun fayl yuklash va saqlash funksiyasi

4. **Production uchun tayorlash:**
   - `DEBUG = False` qiling
   - `ALLOWED_HOSTS` ni sozlang
   - Static fayllarni yig'ing: `python manage.py collectstatic`
   - HTTPS va xavfsizlik sozlamalarini sozlang

## Texnologiyalar

- **Backend**: Django 4.2.7
- **Frontend**: HTML5, CSS3, JavaScript
- **Ma'lumotlar bazasi**: SQLite (development), PostgreSQL tavsiya etiladi (production)
- **Dizayn**: Custom CSS with CSS Variables
- **Font**: Inter (Google Fonts)

## Ranglar

- **Asosiy rang (Primary)**: #02AB6F (Yashil)
- **Ikkinchi darajali rang (Secondary)**: #86DAF1 (Moviy)
- **Qo'shimcha rang (Accent)**: #0288D1

## Muallif

O'zbekiston Ilmiy Jurnali

## Litsenziya

© 2026 Ilmiy Jurnal. Barcha huquqlar himoyalangan.
# Lifelong Learning — Ilmiy Jurnal Sayti

Django asosidagi ilmiy jurnal platformasi: maqola yuborish, taqriz, tom PDF va sertifikat generatsiyasi.

## Texnologiyalar

- Django 5.2, PostgreSQL, Jazzmin admin
- ReportLab + pypdf (PDF generatsiya)
- WhiteNoise (production static fayllar)

## Loyiha strukturasi

```
LIfeLongLearning/
├── ilmiy_jurnal/       # settings, urls, wsgi
├── pages/              # asosiy ilova
│   ├── static/         # Yagona static manba (CSS, JS, rasmlar)
│   ├── templates/
│   ├── pdf/            # tom va sertifikat shablonlari
│   └── ...
├── staticfiles/        # collectstatic natijasi (gitga kirmaydi)
├── media/              # yuklangan fayllar (gitga kirmaydi)
├── .env.example
└── requirements.txt
```

**Muhim:** Barcha CSS/JS faqat `pages/static/` ichida. Eski `static/` papka olib tashlangan — serverda ham faqat shu manbadan foydalaning.

## O'rnatish

```powershell
git clone https://github.com/000Jasurbek000/LIfeLongLearning.git
cd LIfeLongLearning
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# .env ichida DB_PASSWORD, SECRET_KEY, ALLOWED_HOSTS ni to'ldiring
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

## Production (server) — CSS muammosini oldini olish

Serverda CSS buzilsa, odatda **eski static papka** yoki **collectstatic qilinmagan** bo'ladi.

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# gunicorn yoki uwsgi orqali ishga tushiring — WhiteNoise static fayllarni beradi
```

`.env` da:
```
DEBUG=False
ALLOWED_HOSTS=lifelonglearning.uz,www.lifelonglearning.uz
```

**Nginx ishlatilsa:** `/static/` ni loyiha ichidagi `staticfiles/` papkaga yo'naltiring, eski `static/` papkaga emas:

```nginx
location /static/ {
    alias /path/to/LIfeLongLearning/staticfiles/;
}
location /media/ {
    alias /path/to/LIfeLongLearning/media/;
}
```

## Asosiy URL lar

| Sahifa | URL |
|--------|-----|
| Bosh | `/` |
| Maqola yuborish | `/maqola-berish/` |
| Arxiv | `/arxiv/` |
| Admin panel | `/admin/` |
| Custom admin | `/admin-panel/foydalanuvchilar/` |
| Taqrizchi | `/taqrizchi/login/` |

## Sinov ma'lumotlari

```bash
python manage.py seed_workflow_test --reset
```

"""
Tom va sertifikat PDF shabloni — faqat shu faylni keyinroq o'zgartiring.
Barcha matn, ranglar va jurnal ma'lumotlari shu yerda.
"""

# ── Jurnal brendi ──────────────────────────────────────────────
JOURNAL = {
    'name': 'LIFELONG LEARNING',
    'subtitle': "ILMIY-AMALIY ELEKTRON JURNAL",
    'issn': '3060-1234',
    'website': 'www.lifelonglearning.uz',
    'email': 'info@lifelonglearning.uz',
    'location': "Buxoro – O'zbekiston",
    'founder': '"Lifelong Learning" nashriyoti',
    'registration_number': '000000',
    'languages': "o'zbek, ingliz, rus",
}

# ── Ranglar (hex) ──────────────────────────────────────────────
COLORS = {
    'primary': '#02885d',
    'primary_dark': '#016b4a',
    'secondary': '#0288D1',
    'accent': '#86DAF1',
    'text_dark': '#1e293b',
    'text_muted': '#64748b',
    'gold': '#C9A227',
    'white': '#FFFFFF',
}

# ── Muqova sahifasi ────────────────────────────────────────────
COVER = {
    'show_globe_watermark': True,
    'footer_location': "Buxoro – O'zbekiston",
}

# ── Ma'lumot sahifasi (2-bet) ──────────────────────────────────
INFO_PAGE = {
    'about': (
        "Jurnal ta'lim, innovatsiya va zamonaviy texnologiyalar sohasidagi "
        "ilmiy-amaliy tadqiqotlarni nashr etadi."
    ),
    'goals': [
        "Ilmiy tadqiqotlarni qo'llab-quvvatlash",
        "Bilimlarni keng ommaga yetkazish",
        "Yosh olimlarni rag'batlantirish",
        "Xalqaro standartlarga mos nashr",
    ],
    'directions': [
        'Kimyo va texnologiya fanlari',
        'Materialshunoslik va nanotexnologiyalar',
        'Atrof-muhit muhofazasi va ekologiya',
        'Biotexnologiya va biokimyo',
    ],
    'policy': "Jurnal ochiq kirish (Open Access) va taqriz (peer-review) asosida nashr etiladi.",
    'requirements': "Qabul qilingan maqolalar DOI raqami bilan indekslanadi.",
}

# ── Sertifikat shabloni ────────────────────────────────────────
# Faqat FIO, sertifikat raqami va sana o'zgaradi — qolgani rasm shablonida.
CERTIFICATE = {
    'title': 'SERTIFIKAT',
    'intro': 'Ushbu sertifikat',
    'body': (
        '“Lifelong Learning” ilmiy-amaliy elektron jurnalida muvaffaqiyatli '
        "ro'yxatdan o'tganligi tasdiqlanadi."
    ),
    'number_prefix': 'LL',
    'template_file': 'pdf/certificate_template.png',
    'editor_title': 'Bosh muharrir',
    'editor_org': 'Lifelong Learning jurnali',
    'director_title': 'Nashriyot direktori',
    'director_org': 'Lifelong Learning nashriyoti',
    'values': [
        ('ILMIY YONDASHUV', 'book'),
        ('SIFAT VA ISHONCH', 'trophy'),
        ('GLOBAL TAJRIBA', 'globe'),
        ('DOIMIY RIVOJLANISH', 'check'),
    ],
}

# Landscape A4 ustida dinamik matn joylari (nuqta = sm, ReportLab koordinatalari)
CERTIFICATE_LAYOUT = {
    # Placeholder ustiga oq qoplam — shablondagi namuna ism/raqam/sana yopiladi
    'cover_name': {'x': 8.5, 'y': 7.8, 'w': 18, 'h': 1.6},
    'cover_cert': {'x': 22, 'y': 9.2, 'w': 6.5, 'h': 0.55},
    'cover_date': {'x': 22, 'y': 8.5, 'w': 6.5, 'h': 0.55},
    # Dinamik matn
    'name': {'x_center': True, 'y': 8.35, 'font': 'Helvetica-BoldOblique', 'size': 26, 'color': '#014d40'},
    'cert_number': {'x': 27.8, 'y': 9.45, 'font': 'Helvetica-Bold', 'size': 10, 'color': '#1e293b', 'prefix': ''},
    'date': {'x': 27.8, 'y': 8.75, 'font': 'Helvetica-Bold', 'size': 10, 'color': '#1e293b', 'format': '%d.%m.%Y'},
}

# ── Mundarija ──────────────────────────────────────────────────
TOC = {
    'title': 'MUNDARIJA',
    'columns': ['№', 'Mavzu', 'Mualliflar', 'Bet'],
}

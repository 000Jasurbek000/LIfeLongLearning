from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q
from django.contrib.auth.models import User


MANUSCRIPT_EXTENSIONS = ['pdf']


class Author(models.Model):
    """Maqola mualliflari - har bir yuboruvchi uchun"""
    
    # Unik identifikatsiya uchun
    full_name = models.CharField('F.I.O', max_length=200)
    email = models.EmailField('Email')
    phone = models.CharField('Telefon raqami', max_length=20)
    
    # Qo'shimcha
    workplace = models.CharField('Ish joyi', max_length=300, blank=True)
    academic_degree = models.CharField('Ilmiy daraja', max_length=100, blank=True)
    
    # Statistika
    total_articles = models.IntegerField('Jami maqolalar', default=0, editable=False)
    approved_articles = models.IntegerField('Tasdiqlangan', default=0, editable=False)
    rejected_articles = models.IntegerField('Rad etilgan', default=0, editable=False)
    pending_articles = models.IntegerField('Kutilmoqda', default=0, editable=False)
    
    # Sana
    first_submission = models.DateTimeField('Birinchi yuborgan vaqti', auto_now_add=True)
    last_submission = models.DateTimeField('Oxirgi yuborgan vaqti', auto_now=True)
    
    class Meta:
        verbose_name = 'Muallif'
        verbose_name_plural = 'Mualliflar'
        ordering = ['-last_submission']
        # Unik constraint - ism, email, telefon bir xil bo'lsa bir xil odam
        unique_together = [['full_name', 'email', 'phone']]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def update_statistics(self):
        """Statistikani yangilash"""
        self.total_articles = self.articles.count()
        self.approved_articles = self.articles.filter(status__in=['approved', 'published']).count()
        self.rejected_articles = self.articles.filter(status='rejected').count()
        self.pending_articles = self.articles.filter(status='pending').count()
        self.save()


class Article(models.Model):
    """Maqola modeli - foydalanuvchilar tomonidan yuborilgan maqolalar"""
    
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Bekor qilingan'),
        ('published', 'Nashr etilgan'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', "To'lanmagan"),
        ('paid', "To'langan"),
        ('refunded', 'Qaytarilgan'),
    ]
    
    CATEGORY_CHOICES = [
        ('chemistry', 'Kimyo fanlari (noorganik, organik, analitik, fizikaviy kimyo)'),
        ('technology', 'Texnologiya fanlari (oziq-ovqat, kimyoviy, neft va gaz texnologiyasi)'),
        ('materials', 'Materialshunoslik va nanotexnologiyalar'),
        ('ecology', 'Atrof-muhit muhofazasi va ekologiya'),
        ('biotechnology', 'Biotexnologiya va biokimyo'),
    ]

    DEGREE_LABELS = {
        'phd': 'PhD',
        'dsc': 'DSc',
        'candidate': 'Fan nomzodi',
        'doctor': 'Fan doktori',
        'none': "Yo'q",
        '': '-',
        None: '-',
    }
    
    # Muallif (unik identifikatsiya)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='articles', verbose_name='Muallif', null=True, blank=True)
    
    # Maqola ma'lumotlari
    title = models.CharField('Maqola nomi', max_length=500)
    category = models.CharField('Yo\'nalish', max_length=50, choices=CATEGORY_CHOICES, default='chemistry')
    pdf_file = models.FileField(
        'Maqola fayli',
        upload_to='articles/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=MANUSCRIPT_EXTENSIONS)],
        help_text='Faqat PDF format qabul qilinadi',
    )
    additional_files = models.FileField(
        "Qo'shimcha fayllar (rasm, jadval va h.k.)",
        upload_to='articles/additional/%Y/%m/',
        blank=True,
        null=True,
        help_text='ZIP yoki RAR formatida'
    )
    abstract = models.TextField('Annotatsiya', blank=True)
    keywords = models.CharField('Kalit so\'zlar', max_length=500, blank=True, help_text='Vergul bilan ajrating')
    
    # Muallif ma'lumotlari (saqlanadi ma'lumot uchun)
    author_name = models.CharField('Muallif FIO', max_length=200)
    author_email = models.EmailField('Email')
    author_phone = models.CharField('Telefon', max_length=20)
    author_degree = models.CharField('Ilmiy daraja', max_length=100, blank=True)
    author_workplace = models.CharField('Ish joyi', max_length=300, blank=True)
    author_position = models.CharField('Lavozim', max_length=200, blank=True)
    author_orcid = models.CharField('ORCID ID', max_length=100, blank=True)
    co_authors = models.CharField(
        "Ham mualliflar", max_length=500, blank=True,
        help_text="Vergul bilan ajrating (masalan: Karimov A., Rahimov B.)",
    )
    
    # Nashr PDF fayllari (avtomatik generatsiya)
    personal_pdf = models.FileField(
        'Shaxsiy nashr PDF', upload_to='generated/personal/%Y/%m/',
        blank=True, null=True, editable=False,
    )
    certificate_pdf = models.FileField(
        'Sertifikat PDF', upload_to='generated/certificates/%Y/%m/',
        blank=True, null=True, editable=False,
    )
    certificate_number = models.CharField('Sertifikat raqami', max_length=50, blank=True)
    doi = models.CharField('DOI', max_length=200, blank=True, help_text='Masalan: 10.1234/example')
    
    # Holat va to'lov
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField("To'lov holati", max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_amount = models.DecimalField("To'lov miqdori", max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateTimeField("To'lov sanasi", null=True, blank=True)
    payment_transaction_id = models.CharField('Tranzaksiya ID', max_length=200, blank=True)
    
    # Rad etish ma'lumotlari
    rejection_reason = models.TextField('Bekor qilish sababi', blank=True)
    rejection_date = models.DateTimeField('Bekor qilish sanasi', null=True, blank=True)
    rejection_notified = models.BooleanField('Email yuborildi', default=False)
    
    # To'lov linki yuborish ma'lumotlari
    payment_link_sent = models.BooleanField("To'lov linki yuborildi", default=False)
    payment_link_sent_at = models.DateTimeField("To'lov linki yuborilgan vaqt", null=True, blank=True)
    payment_link_sent_count = models.IntegerField("To'lov linki yuborilgan soni", default=0)
    
    # Vaqt belgilari
    submitted_at = models.DateTimeField('Yuborilgan vaqt', auto_now_add=True)
    updated_at = models.DateTimeField('O\'zgartirilgan vaqt', auto_now=True)
    approved_at = models.DateTimeField('Tasdiqlangan vaqt', null=True, blank=True)
    published_at = models.DateTimeField('Nashr qilingan vaqt', null=True, blank=True)

    # Tom (Volume)
    volume = models.ForeignKey(
        'Volume', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='volume_articles',
        verbose_name='Tom'
    )
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField('Izohlar (admin uchun)', blank=True)
    views_count = models.IntegerField("Ko'rishlar soni", default=0)
    downloads_count = models.IntegerField('Yuklab olishlar soni', default=0)
    
    class Meta:
        verbose_name = 'Maqola'
        verbose_name_plural = 'Maqolalar'
        ordering = ['-submitted_at']
        
    def __str__(self):
        return f"{self.title} - {self.author_name}"
    
    def get_status_display_color(self):
        """Status ranglarini qaytaradi"""
        colors = {
            'pending': '#FFA500',  # Orange
            'approved': '#28A745',  # Green
            'rejected': '#DC3545',  # Red
            'published': '#007BFF',  # Blue
        }
        return colors.get(self.status, '#6C757D')
    
    def get_payment_status_color(self):
        """To'lov status ranglarini qaytaradi"""
        colors = {
            'pending': '#FFA500',
            'paid': '#28A745',
            'refunded': '#DC3545',
        }
        return colors.get(self.payment_status, '#6C757D')

    def get_author_degree_label(self):
        """Ilmiy daraja qiymatini foydalanuvchiga tushunarli ko'rinishga o'tkazadi"""
        return self.DEGREE_LABELS.get(self.author_degree, self.author_degree or '-')


class EditorialMember(models.Model):
    """Tahririyat a'zolari modeli"""
    
    POSITION_CHOICES = [
        ('editor_in_chief', 'Bosh muharrir'),
        ('deputy_editor', "Bosh muharrir o'rinbosari"),
        ('executive_editor', 'Mas\'ul muharrir'),
        ('section_editor', 'Bo\'lim muharriri'),
        ('member', 'Tahririyat hay\'ati a\'zosi'),
        ('technical_editor', 'Texnik muharrir'),
    ]
    
    # Shaxsiy ma'lumotlar
    full_name = models.CharField('F.I.O', max_length=200)
    position = models.CharField('Lavozim', max_length=50, choices=POSITION_CHOICES)
    academic_degree = models.CharField('Ilmiy daraja', max_length=200, blank=True)
    workplace = models.CharField('Ish joyi', max_length=300)
    
    # Rasm
    photo = models.ImageField('Rasm', upload_to='editorial/%Y/', blank=True, null=True)
    
    # Holat
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Qo\'shilgan sana', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tahririyat a\'zosi'
        verbose_name_plural = 'Tahririyat hay\'ati'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.get_position_display()}"


class RegulatoryDocument(models.Model):
    """Meyoriy hujjatlar modeli"""
    
    image = models.ImageField('Hujjat rasmi', upload_to='regulatory_docs/%Y/%m/')
    
    # Holat
    is_active = models.BooleanField('Faol', default=True)
    
    # Sana
    uploaded_at = models.DateTimeField('Yuklangan sana', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Meyoriy hujjat'
        verbose_name_plural = 'Meyoriy hujjatlar'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Hujjat #{self.pk} - {self.uploaded_at.strftime('%d.%m.%Y')}"


class News(models.Model):
    """Yangiliklar modeli"""
    
    title = models.CharField('Sarlavha', max_length=300)
    slug = models.SlugField('Slug', max_length=300, unique=True, help_text='URL uchun noyob nom (masalan: yangi-laboratoriya-ochildi)')
    category = models.CharField('Kategoriya', max_length=100, help_text='Masalan: Tadbirlar, Yangiliklar, Ilmiy')
    
    # Asosiy content
    image = models.ImageField('Rasm', upload_to='news/%Y/%m/')
    excerpt = models.TextField('Qisqacha', max_length=500, help_text='Qisqa tavsif (ro\'yxatda ko\'rsatiladi)')
    content = models.TextField('To\'liq matn')
    
    # Meta ma'lumotlar
    author = models.CharField('Muallif', max_length=200, default='Admin')
    views = models.IntegerField('Ko\'rishlar soni', default=0, editable=False)
    
    # Sana va holat
    published_date = models.DateTimeField('Nashr sanasi', auto_now_add=True)
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Yangilik'
        verbose_name_plural = 'Yangiliklar'
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title


class Announcement(models.Model):
    """E'lonlar modeli"""
    
    CATEGORY_CHOICES = [
        ('muhim', 'Muhim e\'lon'),
        ('umumiy', 'Umumiy ma\'lumot'),
        ('eslatma', 'Eslatma'),
        ('imtihon', 'Imtihon e\'loni'),
        ('konferensiya', 'Konferensiya'),
        ('konkurs', 'Konkurs'),
        ('muddat', 'Muddat e\'loni'),
        ('boshqa', 'Boshqa'),
    ]
    
    title = models.CharField('Sarlavha', max_length=300)
    slug = models.SlugField('Slug', max_length=300, unique=True, help_text='URL uchun noyob nom')
    category = models.CharField('Kategoriya', max_length=50, choices=CATEGORY_CHOICES, default='umumiy')
    
    # Asosiy content
    excerpt = models.TextField('Qisqacha', max_length=500, help_text='Qisqa tavsif')
    content = models.TextField('To\'liq matn')
    author = models.CharField('Muallif', max_length=200, default='Tahririyat', blank=True)
    
    # Sana va muddatlar
    published_date = models.DateTimeField('E\'lon qo\'shilgan sana', auto_now_add=True)
    validity_start = models.DateField('Amal qilish boshlanishi', null=True, blank=True, help_text='E\'lon qachondan amal qila boshlaydi')
    validity_end = models.DateField('Amal qilish tugashi', null=True, blank=True, help_text='E\'lon qachongacha amal qiladi')
    
    # Holat
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'E\'lon'
        verbose_name_plural = 'E\'lonlar'
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title
    
    def get_icon(self):
        """Kategoriyaga qarab avtomatik icon qaytarish"""
        icon_map = {
            'muhim': 'warning',
            'umumiy': 'info',
            'eslatma': 'info',
            'imtihon': 'document',
            'konferensiya': 'info',
            'konkurs': 'document',
            'muddat': 'warning',
            'boshqa': 'info',
        }
        return icon_map.get(self.category, 'info')
    
    def get_priority(self):
        """Kategoriyaga qarab avtomatik muhimlik darajasi"""
        priority_map = {
            'muhim': 'yuqori',
            'muddat': 'yuqori',
            'imtihon': 'orta',
            'konkurs': 'orta',
            'konferensiya': 'orta',
            'eslatma': 'past',
            'umumiy': 'past',
            'boshqa': 'past',
        }
        return priority_map.get(self.category, 'orta')
    
    def is_valid(self):
        """E'lon hali amal qiladimi?"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.validity_end:
            return today <= self.validity_end
        return True
    
    def validity_status(self):
        """Amal qilish holati"""
        if not self.validity_end:
            return 'Muddat belgilanmagan'
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if today > self.validity_end:
            return 'Muddati o\'tgan'
        elif today == self.validity_end:
            return 'Bugun tugaydi'
        else:
            days_left = (self.validity_end - today).days
            return f'{days_left} kun qoldi'


# ===================== TOMLAR (VOLUMES) =====================

class Volume(models.Model):
    """Jurnal tomi - maqolalar bir tomda chop etiladi"""
    STATUS_CHOICES = [
        ('draft',     'Tayyorlanmoqda'),
        ('active',    'Faol (maqola qabul qilmoqda)'),
        ('published', 'Nashr etilgan'),
    ]

    SUBJECT_CHOICES = [
        ('chemistry',     'Kimyo fanlari'),
        ('technology',    'Texnologiya fanlari'),
        ('materials',     'Materialshunoslik va nanotexnologiyalar'),
        ('ecology',       'Atrof-muhit muhofazasi va ekologiya'),
        ('biotechnology', 'Biotexnologiya va biokimyo'),
        ('mixed',         'Aralash yo\'nalishlar'),
    ]

    title          = models.CharField('Tom nomi', max_length=300,
                                      help_text='Masalan: 2026-yil, 5-tom, 2-son')
    slug           = models.SlugField('Slug', max_length=300, unique=True)
    subject        = models.CharField('Fan yo\'nalishi', max_length=50,
                                      choices=SUBJECT_CHOICES, default='mixed', blank=True)
    year           = models.IntegerField('Yil', default=2026)
    volume_number  = models.IntegerField('Tom raqami', default=1)
    issue_number   = models.IntegerField('Son raqami', default=1)
    max_articles   = models.IntegerField('Maqolalar soni (belgilangan)',
                                         default=10,
                                         help_text='Tomga necha maqola kirishi mumkin')
    status         = models.CharField('Holat', max_length=20,
                                      choices=STATUS_CHOICES, default='draft')
    cover_image    = models.ImageField('Muqova rasmi', upload_to='volumes/covers/',
                                       blank=True, null=True)
    pdf_file       = models.FileField('To\'liq tom PDF', upload_to='volumes/pdf/',
                                      blank=True, null=True,
                                      help_text='Admin tomonidan tahrirlangan va chop etilgan tom PDF')
    description    = models.TextField('Tavsif', blank=True)
    published_at   = models.DateTimeField('Nashr sanasi', null=True, blank=True)
    views_count    = models.IntegerField("Ko'rishlar soni", default=0)
    created_at     = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at     = models.DateTimeField('Yangilangan', auto_now=True)

    class Meta:
        verbose_name = 'Tom'
        verbose_name_plural = 'Tomlar'
        ordering = ['-year', '-volume_number', '-issue_number']

    def __str__(self):
        return self.title

    @property
    def articles_count(self):
        return self.volume_articles.count() + self.manual_articles.count()

    @property
    def submitted_articles_count(self):
        return self.volume_articles.count()

    @property
    def manual_articles_count(self):
        return self.manual_articles.count()

    @property
    def remaining_slots(self):
        return max(0, self.max_articles - self.articles_count)

    @property
    def is_full(self):
        return self.articles_count >= self.max_articles

    @property
    def fill_percent(self):
        if self.max_articles == 0:
            return 0
        return min(100, int(self.articles_count / self.max_articles * 100))


# ===================== TOM MAQOLALARI (QOLDA KIRITILGAN) =====================

class VolumeArticle(models.Model):
    """Tomga qo'lda (admin tomonidan) kiritilgan maqola"""

    CATEGORY_CHOICES = [
        ('chemistry',     'Kimyo fanlari'),
        ('technology',    'Texnologiya fanlari'),
        ('materials',     'Materialshunoslik va nanotexnologiyalar'),
        ('ecology',       'Atrof-muhit muhofazasi va ekologiya'),
        ('biotechnology', 'Biotexnologiya va biokimyo'),
    ]

    volume       = models.ForeignKey(Volume, on_delete=models.CASCADE,
                                     related_name='manual_articles',
                                     verbose_name='Tom')
    category     = models.CharField('Fan yo\'nalishi', max_length=50,
                                    choices=CATEGORY_CHOICES, default='chemistry')
    title        = models.CharField('Maqola mavzusi', max_length=500)
    slug         = models.SlugField('Slug', max_length=300, blank=True)
    authors      = models.CharField('Avtorlari', max_length=500,
                                    help_text='Masalan: Karimov A., Rahimov B.')
    published_date = models.DateField('Nashr sanasi', null=True, blank=True)
    abstract     = models.TextField('Annotatsiya (ixtiyoriy)', blank=True)
    keywords     = models.CharField('Kalit so\'zlar', max_length=500, blank=True,
                                    help_text='Vergul bilan ajrating')
    references   = models.TextField('Adabiyotlar ro\'yxati', blank=True,
                                    help_text='Har bir manba yangi qatordan')
    doi          = models.CharField('DOI', max_length=200, blank=True)
    pages        = models.CharField('Sahifalar', max_length=50, blank=True,
                                    help_text='Masalan: 12-18')
    pdf_file     = models.FileField('Maqola PDFi', upload_to='volume_articles/pdf/',
                                    blank=True, null=True,
                                    help_text='Alohida maqola PDF fayli')
    views_count  = models.IntegerField("Ko'rishlar soni", default=0)
    created_at   = models.DateTimeField('Qo\'shilgan vaqt', auto_now_add=True)

    class Meta:
        verbose_name = 'Tom maqolasi'
        verbose_name_plural = 'Tom maqolalari'
        ordering = ['published_date', 'title']
        unique_together = [['volume', 'slug']]

    def __str__(self):
        return f"{self.title} — {self.authors}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'maqola'
            slug = base
            counter = 1
            qs = VolumeArticle.objects.filter(volume=self.volume, slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.exists():
                slug = f'{base}-{counter}'
                counter += 1
                qs = VolumeArticle.objects.filter(volume=self.volume, slug=slug)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
            self.slug = slug
        super().save(*args, **kwargs)


# ===================== TAQRIZCHILAR =====================

class Reviewer(models.Model):
    """Taqrizchi - admin tomonidan yaratilgan, o'z profili va maqola ko'rish imkoniyatiga ega"""
    SPECIALIZATION_CHOICES = [
        ('chemistry',    'Kimyo fanlari'),
        ('technology',   'Texnologiya fanlari'),
        ('materials',    'Materialshunoslik va nanotexnologiyalar'),
        ('ecology',      'Atrof-muhit muhofazasi va ekologiya'),
        ('biotechnology','Biotexnologiya va biokimyo'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='reviewer_profile',
        verbose_name='Foydalanuvchi'
    )
    full_name       = models.CharField('F.I.O', max_length=200)
    position        = models.CharField('Lavozimi', max_length=200, blank=True)
    specialization  = models.CharField('Yo\'nalish', max_length=50,
                                       choices=SPECIALIZATION_CHOICES,
                                       default='chemistry')
    photo           = models.ImageField('Rasm', upload_to='reviewers/', blank=True, null=True)
    created_at      = models.DateTimeField('Yaratilgan', auto_now_add=True)

    class Meta:
        verbose_name = 'Taqrizchi'
        verbose_name_plural = 'Taqrizchilar'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    @property
    def pending_count(self):
        return self.reviews.filter(status='pending').count()

    @property
    def reviewed_count(self):
        return self.reviews.exclude(status='pending').count()


class ArticleReview(models.Model):
    """Maqolaga taqrizchi biriktirish va uning qarori"""
    STATUS_CHOICES = [
        ('pending',  'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    ]
    article         = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reviews')
    reviewer        = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='reviews')
    status          = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason= models.TextField('Rad etish sababi', blank=True)
    rejection_file  = models.FileField('Fayl', upload_to='reviews/%Y/%m/', blank=True, null=True)
    assigned_at     = models.DateTimeField('Biriktirilgan vaqt', auto_now_add=True)
    reviewed_at     = models.DateTimeField('Ko\'rib chiqilgan vaqt', null=True, blank=True)

    class Meta:
        verbose_name = 'Taqriz'
        verbose_name_plural = 'Taqrizlar'
        unique_together = [['article', 'reviewer']]
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.reviewer.full_name} → {self.article.title[:40]}"


# ===================== OBUNACHLAR =====================

class Subscriber(models.Model):
    """Xabar obunachilari - newsletter yoki maqola yuborgan foydalanuvchilar"""

    SOURCE_CHOICES = [
        ('newsletter', 'Obuna formasi'),
        ('article',    'Maqola yuborish'),
    ]

    full_name  = models.CharField('F.I.O', max_length=200)
    email      = models.EmailField('Email', unique=True)
    source     = models.CharField('Manba', max_length=20, choices=SOURCE_CHOICES, default='newsletter')
    is_active  = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Obuna bo\'lgan vaqt', auto_now_add=True)

    class Meta:
        verbose_name = 'Obunachi'
        verbose_name_plural = 'Obunachlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

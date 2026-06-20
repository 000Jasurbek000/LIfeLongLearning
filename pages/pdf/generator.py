"""Tom, shaxsiy nashr va sertifikat PDF generatsiyasi."""

from __future__ import annotations

import io
import re
import tempfile
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .volume_template import CERTIFICATE, CERTIFICATE_LAYOUT, COLORS, COVER, INFO_PAGE, JOURNAL, TOC

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter  # fallback


def _hex(color: str):
    color = color.lstrip('#')
    return colors.HexColor(f'#{color}')


def parse_authors(author_name: str, co_authors: str = '') -> list[str]:
    """Mualliflar ro'yxatini ajratish."""
    raw = author_name or ''
    if co_authors:
        raw = f'{raw}, {co_authors}'
    parts = re.split(r'[,;]|\s+va\s+|\s+and\s+', raw, flags=re.IGNORECASE)
    result = []
    for part in parts:
        name = part.strip()
        if name and name not in result:
            result.append(name)
    return result or [author_name or 'Muallif']


def next_certificate_number(article_id: int, author_index: int = 0, total_authors: int = 1) -> str:
    """Har bir muallif uchun alohida sertifikat raqami."""
    year = timezone.now().year
    base = f"{CERTIFICATE['number_prefix']}-{year}-{article_id:06d}"
    if total_authors > 1:
        return f'{base}-{author_index + 1:02d}'
    return base


def _certificate_template_path() -> Path | None:
    rel = CERTIFICATE.get('template_file', 'pdf/certificate_template.png')
    path = settings.BASE_DIR / 'pages' / 'static' / rel
    if path.exists():
        return path
    return None


def _logo_path() -> Path | None:
    candidates = [
        settings.BASE_DIR / 'pages' / 'static' / 'image' / 'LOGO.png',
        settings.BASE_DIR / 'pages' / 'static' / 'image' / 'LOGO 02.png',
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _article_pdf_path(article) -> Path | None:
    if article.pdf_file and article.pdf_file.name:
        path = Path(article.pdf_file.path)
        if path.exists():
            return path
    return None


def _volume_articles_ordered(volume):
    """Tomdagi maqolalar — tasdiqlangan vaqti bo'yicha."""
    from pages.models import Article

    return list(
        volume.volume_articles.filter(status='published')
        .order_by('approved_at', 'pk')
    )


class VolumePDFBuilder:
    """Tom PDF yig'uvchi."""

    def __init__(self, volume, articles=None):
        self.volume = volume
        self.articles = articles if articles is not None else _volume_articles_ordered(volume)
        self.page_map: dict[int, tuple[int, int]] = {}  # article_id -> (start, end)

    def build(self, output_path: Path, *, single_article_id: int | None = None):
        """single_article_id berilsa — faqat shu maqola bilan shaxsiy nashr."""
        if single_article_id:
            self.articles = [a for a in self.articles if a.pk == single_article_id]

        # Sahifa raqamlarini oldindan hisoblash (mundarija uchun)
        front_page_count = 3
        current = front_page_count + 1
        for article in self.articles:
            article_path = _article_pdf_path(article)
            if not article_path:
                continue
            reader = PdfReader(str(article_path))
            start = current
            current += len(reader.pages)
            self.page_map[article.pk] = (start, current - 1)

        front = self._build_front_pages()
        merged = PdfWriter()

        for page in front:
            merged.add_page(page)

        for article in self.articles:
            article_path = _article_pdf_path(article)
            if not article_path:
                continue
            reader = PdfReader(str(article_path))
            for page in reader.pages:
                merged.add_page(page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('wb') as f:
            merged.write(f)
        return output_path

    def _build_front_pages(self) -> list:
        """Muqova + ma'lumot + mundarija."""
        pages = []
        for builder in (self._cover_page, self._info_page, self._toc_page):
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            builder(c)
            c.save()
            buf.seek(0)
            reader = PdfReader(buf)
            pages.append(reader.pages[0])
        return pages

    def _cover_page(self, c: canvas.Canvas):
        w, h = A4
        primary = _hex(COLORS['primary'])
        secondary = _hex(COLORS['secondary'])

        # Pastki to'lqin
        c.setFillColor(primary)
        c.rect(0, 0, w, h * 0.28, fill=1, stroke=0)
        c.setFillColor(_hex(COLORS['primary_dark']))
        c.rect(0, 0, w, h * 0.12, fill=1, stroke=0)

        # Logo
        logo = _logo_path()
        if logo:
            c.drawImage(str(logo), 2 * cm, h - 4 * cm, width=3.5 * cm, height=1.8 * cm, preserveAspectRatio=True, mask='auto')

        c.setFillColor(_hex(COLORS['text_dark']))
        c.setFont('Helvetica-Bold', 9)
        c.drawString(6 * cm, h - 2.6 * cm, JOURNAL['name'])
        c.setFont('Helvetica', 8)
        c.drawRightString(w - 2 * cm, h - 2.4 * cm, f"ISSN {JOURNAL['issn']}")
        c.drawRightString(w - 2 * cm, h - 3.1 * cm, JOURNAL['website'])

        c.setStrokeColor(secondary)
        c.setLineWidth(1)
        c.line(2 * cm, h - 3.6 * cm, w - 2 * cm, h - 3.6 * cm)

        c.setFillColor(primary)
        c.setFont('Helvetica-Bold', 28)
        c.drawCentredString(w / 2, h / 2 + 1.5 * cm, JOURNAL['name'])

        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(w / 2, h / 2 + 0.3 * cm, JOURNAL['subtitle'])

        c.setStrokeColor(primary)
        c.line(w / 2 - 4 * cm, h / 2, w / 2 + 4 * cm, h / 2)

        # Tom ma'lumotlari
        y = h * 0.42
        stats = [
            ('JILD', str(self.volume.volume_number)),
            ('SON', str(self.volume.issue_number)),
            (self._month_label(), str(self.volume.year)),
        ]
        x_positions = [w * 0.25, w * 0.5, w * 0.75]
        for i, (label, value) in enumerate(stats):
            cx = x_positions[i]
            c.setStrokeColor(secondary)
            c.circle(cx, y, 1.2 * cm, stroke=1, fill=0)
            c.setFillColor(_hex(COLORS['text_muted']))
            c.setFont('Helvetica', 8)
            c.drawCentredString(cx, y - 2 * cm, label)
            c.setFillColor(_hex(COLORS['text_dark']))
            c.setFont('Helvetica-Bold', 16)
            c.drawCentredString(cx, y - 0.15 * cm, value)

        c.setFillColor(_hex(COLORS['white']))
        c.setFont('Helvetica', 9)
        c.drawCentredString(w / 2, 1.5 * cm, COVER['footer_location'])
        c.showPage()

    def _month_label(self) -> str:
        months = {
            1: 'YAN', 2: 'FEV', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'IYUN',
            7: 'IYUL', 8: 'AVG', 9: 'SEN', 10: 'OKT', 11: 'NOY', 12: 'DEK',
        }
        dt = self.volume.published_at or timezone.now()
        return months.get(dt.month, 'SON')

    def _info_page(self, c: canvas.Canvas):
        w, h = A4
        primary = _hex(COLORS['primary'])
        c.setFillColor(primary)
        c.setFont('Helvetica-Bold', 14)
        c.drawCentredString(w / 2, h - 2.5 * cm, f"{JOURNAL['name']}: {JOURNAL['subtitle']}")
        c.setFont('Helvetica', 10)
        c.setFillColor(_hex(COLORS['text_muted']))
        c.drawCentredString(
            w / 2, h - 3.2 * cm,
            f"Vol. {self.volume.volume_number}, No. {self.volume.issue_number} ({self.volume.year})",
        )

        y = h - 4.5 * cm
        sections = [
            ('Jurnal haqida', INFO_PAGE['about']),
            ('Maqsad va vazifalar', '\n'.join(f'• {g}' for g in INFO_PAGE['goals'])),
            ("Yo'nalishlar", '\n'.join(f'• {d}' for d in INFO_PAGE['directions'])),
            ('Nashr etish siyosati', INFO_PAGE['policy']),
            ('Maqolalar talablari', INFO_PAGE['requirements']),
            ('Aloqa', f"{JOURNAL['website']}\n{JOURNAL['email']}\n{JOURNAL['location']}"),
        ]
        c.setFillColor(_hex(COLORS['text_dark']))
        for title, body in sections:
            c.setFont('Helvetica-Bold', 10)
            c.drawString(2 * cm, y, title)
            y -= 0.5 * cm
            c.setFont('Helvetica', 9)
            for line in body.split('\n'):
                c.drawString(2.3 * cm, y, line[:90])
                y -= 0.42 * cm
            y -= 0.3 * cm

        c.setFillColor(_hex(COLORS['accent']))
        c.rect(1.5 * cm, 2.5 * cm, w - 3 * cm, 3.5 * cm, fill=1, stroke=0)
        c.setFillColor(_hex(COLORS['text_dark']))
        c.setFont('Helvetica-Bold', 9)
        c.drawString(2 * cm, 5.2 * cm, 'Tahririyat kengashi')
        c.setFont('Helvetica', 8)
        c.drawString(2 * cm, 4.7 * cm, f"ISSN: {JOURNAL['issn']}  |  Muassis: {JOURNAL['founder']}")
        c.drawString(2 * cm, 4.2 * cm, f"Nashr tili: {JOURNAL['languages']}")
        c.showPage()

    def _toc_page(self, c: canvas.Canvas):
        w, h = A4
        primary = _hex(COLORS['primary'])
        c.setFillColor(primary)
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(w / 2, h - 2.5 * cm, TOC['title'])

        y = h - 4 * cm
        c.setFont('Helvetica-Bold', 9)
        c.drawString(2 * cm, y, TOC['columns'][0])
        c.drawString(2.8 * cm, y, TOC['columns'][1])
        c.drawString(12 * cm, y, TOC['columns'][2])
        c.drawString(w - 3 * cm, y, TOC['columns'][3])
        y -= 0.6 * cm
        c.setStrokeColor(_hex(COLORS['text_muted']))
        c.line(2 * cm, y, w - 2 * cm, y)
        y -= 0.5 * cm

        c.setFont('Helvetica', 8)
        c.setFillColor(_hex(COLORS['text_dark']))
        for idx, article in enumerate(self.articles, start=1):
            pages = self.page_map.get(article.pk)
            page_str = f"{pages[0]}-{pages[1]}" if pages else '—'
            title = article.title[:55] + ('…' if len(article.title) > 55 else '')
            authors = article.author_name[:35] + ('…' if len(article.author_name) > 35 else '')
            c.drawString(2 * cm, y, str(idx))
            c.drawString(2.8 * cm, y, title)
            c.drawString(12 * cm, y, authors)
            c.drawRightString(w - 2 * cm, y, page_str)
            y -= 0.55 * cm
            if y < 3 * cm:
                c.showPage()
                y = h - 3 * cm

            # Kalit so'zlar
            if article.keywords:
                c.setFillColor(_hex(COLORS['text_muted']))
                c.setFont('Helvetica-Oblique', 7)
                c.drawString(2.8 * cm, y, f"Kalit so'zlar: {article.keywords[:70]}")
                y -= 0.45 * cm
                c.setFillColor(_hex(COLORS['text_dark']))
                c.setFont('Helvetica', 8)

            # Annotatsiya qisqacha
            if article.abstract:
                c.setFont('Helvetica-Oblique', 7)
                abstract = article.abstract[:120] + ('…' if len(article.abstract) > 120 else '')
                c.drawString(2.8 * cm, y, abstract)
                y -= 0.5 * cm
                c.setFont('Helvetica', 8)

        c.showPage()


def build_certificate_pdf(
    author_entries: list[tuple[str, str]],
    issue_date: date | None = None,
) -> bytes:
    """
    Rasm shablon ustiga faqat FIO, sertifikat raqami va sanani chizadi.
    author_entries: [(ism, sertifikat_raqami), ...]
    """
    issue_date = issue_date or timezone.now().date()
    buf = io.BytesIO()
    page_size = landscape(A4)
    w, h = page_size
    template = _certificate_template_path()
    layout = CERTIFICATE_LAYOUT

    c = canvas.Canvas(buf, pagesize=page_size)

    for author_name, cert_number in author_entries:
        if template:
            c.drawImage(str(template), 0, 0, width=w, height=h, preserveAspectRatio=False, mask='auto')
        else:
            c.setFillColor(_hex(COLORS['white']))
            c.rect(0, 0, w, h, fill=1, stroke=0)

        # Shablondagi namuna matnni yopish
        for cover_key in ('cover_name', 'cover_cert', 'cover_date'):
            box = layout.get(cover_key)
            if not box:
                continue
            c.setFillColor(colors.white)
            c.rect(box['x'] * cm, box['y'] * cm, box['w'] * cm, box['h'] * cm, fill=1, stroke=0)

        # FIO
        name_cfg = layout['name']
        c.setFillColor(_hex(name_cfg['color']))
        c.setFont(name_cfg['font'], name_cfg['size'])
        c.drawCentredString(w / 2, name_cfg['y'] * cm, author_name)

        # Sertifikat raqami
        cert_cfg = layout['cert_number']
        c.setFillColor(_hex(cert_cfg['color']))
        c.setFont(cert_cfg['font'], cert_cfg['size'])
        c.drawRightString(cert_cfg['x'] * cm, cert_cfg['y'] * cm, cert_number)

        # Sana
        date_cfg = layout['date']
        c.setFillColor(_hex(date_cfg['color']))
        c.setFont(date_cfg['font'], date_cfg['size'])
        date_str = issue_date.strftime(date_cfg.get('format', '%d.%m.%Y'))
        c.drawRightString(date_cfg['x'] * cm, date_cfg['y'] * cm, date_str)

        c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()


def generate_and_save_volume_pdf(volume) -> bool:
    """To'liq tom PDF ni yaratib saqlaydi."""
    articles = _volume_articles_ordered(volume)
    if not articles:
        return False

    builder = VolumePDFBuilder(volume, articles)
    # Avvalo sahifalar xaritasini hisoblash uchun ikki bosqich
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        builder.build(tmp_path)
        # Mundarija sahifalarini qayta yaratish kerak — soddalashtirilgan: bir marta build yetarli
        pdf_bytes = tmp_path.read_bytes()
        filename = f"volume_{volume.slug}.pdf"
        volume.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        return True
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def generate_and_save_personal_pdf(article) -> bool:
    """Muallif uchun shaxsiy nashr PDF."""
    if not article.volume:
        return False

    builder = VolumePDFBuilder(article.volume, [article])
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        builder.build(tmp_path, single_article_id=article.pk)
        pdf_bytes = tmp_path.read_bytes()
        filename = f"personal_{article.pk}.pdf"
        article.personal_pdf.save(filename, ContentFile(pdf_bytes), save=False)
        article.save(update_fields=['personal_pdf'])
        return True
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def generate_and_save_certificate_pdf(article) -> bool:
    """Barcha mualliflar uchun sertifikat PDF (bitta fayl, har biri alohida bet)."""
    authors = parse_authors(article.author_name, article.co_authors)
    issue_date = (article.approved_at or timezone.now()).date()
    entries = []
    for idx, name in enumerate(authors):
        cert_num = next_certificate_number(article.pk, idx, len(authors))
        entries.append((name, cert_num))
    # Asosiy raqam — birinchi muallifniki
    article.certificate_number = entries[0][1]
    pdf_bytes = build_certificate_pdf(entries, issue_date)
    filename = f"certificate_{article.pk}.pdf"
    article.certificate_pdf.save(filename, ContentFile(pdf_bytes), save=False)
    article.save(update_fields=['certificate_pdf', 'certificate_number'])
    return True


def publish_article_to_volume(article, volume=None):
    """
    Maqolani tomga biriktirib, barcha PDF larni generatsiya qiladi.
    """
    from pages.models import Volume

    if volume is None:
        volume = Volume.objects.filter(status='active').order_by('-year', '-volume_number').first()
    if not volume:
        raise ValueError("Faol tom topilmadi. Admin paneldan faol tom yarating.")

    if volume.is_full:
        raise ValueError(f"Tom to'lgan ({volume.max_articles} ta limit).")

    article.volume = volume
    article.status = 'published'
    if not article.approved_at:
        article.approved_at = timezone.now()
    if not article.published_at:
        article.published_at = timezone.now()
    article.save()

    generate_and_save_personal_pdf(article)
    generate_and_save_certificate_pdf(article)
    generate_and_save_volume_pdf(volume)

    if article.author:
        article.author.update_statistics()
    return article

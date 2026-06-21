"""DB modellarini shablonlar uchun mos formatga o'tkazish."""

from __future__ import annotations

from calendar import month_name
from types import SimpleNamespace

from django.conf import settings
from django.utils.text import slugify

MONTHS_UZ = {
    1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel', 5: 'May', 6: 'Iyun',
    7: 'Iyul', 8: 'Avgust', 9: 'Sentyabr', 10: 'Oktyabr', 11: 'Noyabr', 12: 'Dekabr',
}

SUBJECT_LABELS = {
    'chemistry': 'Kimyo va texnologiya',
    'technology': 'Texnologiya fanlari',
    'materials': 'Materialshunoslik va nanotexnologiyalar',
    'ecology': 'Atrof-muhit muhofazasi va ekologiya',
    'biotechnology': 'Biotexnologiya va biokimyo',
    'mixed': 'Kimyo va texnologiya',
}


def _media_url(file_field):
    if file_field and hasattr(file_field, 'url'):
        return file_field.url
    return ''


def _format_date(value):
    if not value:
        return ''
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')
    return str(value)


def _month_label(value):
    if not value:
        return ''
    if hasattr(value, 'month'):
        return MONTHS_UZ.get(value.month, month_name[value.month])
    return ''


def present_news(news):
    return SimpleNamespace(
        title=news.title,
        slug=news.slug,
        category=news.category,
        image=_media_url(news.image),
        excerpt=news.excerpt,
        content=news.content,
        author=news.author,
        views=news.views,
        date=news.published_date,
        published_date=news.published_date,
    )


def present_announcement(announcement):
    category_display = announcement.get_category_display() if hasattr(announcement, 'get_category_display') else announcement.category
    return SimpleNamespace(
        title=announcement.title,
        slug=announcement.slug,
        category=category_display,
        excerpt=announcement.excerpt,
        content=announcement.content,
        author=announcement.author or 'Tahririyat',
        date=_format_date(announcement.published_date),
        start_date=_format_date(announcement.validity_start),
        end_date=_format_date(announcement.validity_end),
        priority=announcement.get_priority(),
        icon=announcement.get_icon(),
        attachment=None,
    )


def _article_keywords(raw):
    if not raw:
        return []
    return [part.strip() for part in raw.split(',') if part.strip()]


def _article_references(raw):
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _build_citation(volume, article, authors, title):
    doi = getattr(article, 'doi', '') or ''
    doi_part = f' https://doi.org/{doi}' if doi else ''
    return (
        f'{authors} ({volume.year}). {title}. '
        f'{settings.SITE_NAME}, {volume.issue_number}({volume.volume_number}), '
        f'pp. {getattr(article, "pages", "") or "—"}.{doi_part}'
    )


def present_volume_article(volume, article, *, source='manual'):
    """VolumeArticle yoki Article obyektini arxiv shablon formatiga o'tkazadi."""
    if source == 'manual':
        authors = article.authors
        title = article.title
        slug = article.slug or slugify(title) or f'maqola-{article.pk}'
        date = _format_date(article.published_date)
        abstract = article.abstract or (
            f"Mazkur maqolada {title.lower()} mavzusi nazariy va amaliy jihatdan tahlil qilinadi."
        )
        keywords = _article_keywords(article.keywords)
        references = _article_references(article.references)
        pdf_url = _media_url(article.pdf_file)
        article_id = None
        has_personal_pdf = False
        has_certificate_pdf = False
    else:
        authors = article.author_name
        if article.co_authors:
            authors = f'{authors}, {article.co_authors}'
        title = article.title
        slug = slugify(title) or f'maqola-{article.pk}'
        date = _format_date(article.approved_at or article.submitted_at)
        abstract = article.abstract or (
            f"Mazkur maqolada {title.lower()} mavzusi nazariy va amaliy jihatdan tahlil qilinadi."
        )
        keywords = _article_keywords(article.keywords)
        references = []
        pdf_url = _media_url(article.personal_pdf) or _media_url(article.pdf_file)
        article_id = article.pk
        has_personal_pdf = bool(article.personal_pdf)
        has_certificate_pdf = bool(article.certificate_pdf)

    return SimpleNamespace(
        title=title,
        slug=slug,
        authors=authors,
        display_authors=authors,
        date=date,
        abstract=abstract,
        keywords=keywords or ['ilmiy tadqiqot', 'jurnal'],
        references=references,
        citation=_build_citation(volume, article, authors, title),
        pdf_url=pdf_url or '#',
        pdf_file=article.pdf_file.name if getattr(article, 'pdf_file', None) else '',
        download_url=pdf_url,
        read_url=pdf_url,
        source=source,
        article_id=article_id,
        has_personal_pdf=has_personal_pdf,
        has_certificate_pdf=has_certificate_pdf,
        obj=article,
    )


def present_volume(volume):
    published = volume.published_at or volume.created_at
    manual = list(volume.manual_articles.all())
    submitted = list(
        volume.volume_articles.filter(status='published').order_by('approved_at', 'title')
    )
    articles = [present_volume_article(volume, a, source='manual') for a in manual]
    for article in submitted:
        articles.append(present_volume_article(volume, article, source='submitted'))

    articles.sort(key=lambda item: item.date or '')

    cover = _media_url(volume.cover_image)
    if not cover:
        from django.templatetags.static import static
        cover = static('image/LOGO.png')

    has_volume_pdf = bool(volume.pdf_file)

    return SimpleNamespace(
        slug=volume.slug,
        journal_name=SUBJECT_LABELS.get(volume.subject, volume.title),
        volume=volume.volume_number,
        issue=volume.issue_number,
        year=volume.year,
        month=_month_label(published),
        published_date=_format_date(published),
        article_count=len(articles),
        views=f'{volume.views_count:,}'.replace(',', ' '),
        cover=cover,
        description=volume.description or volume.title,
        articles=articles,
        has_volume_pdf=has_volume_pdf,
        status=volume.status,
        obj=volume,
    )


def _public_volume_queryset():
    from .models import Volume

    return Volume.objects.filter(status__in=['published', 'active']).prefetch_related(
        'manual_articles', 'volume_articles'
    )


def get_published_volumes():
    result = []
    for volume in _public_volume_queryset():
        published_count = volume.volume_articles.filter(status='published').count()
        manual_count = volume.manual_articles.count()
        if volume.status == 'published' or published_count or manual_count:
            result.append(present_volume(volume))
    return result


def get_volume_by_slug(slug):
    volume = _public_volume_queryset().filter(slug=slug).first()
    if not volume:
        return None
    return present_volume(volume)


def find_volume_article(volume_slug, article_slug):
    volume = get_volume_by_slug(volume_slug)
    if not volume:
        return None, None
    for article in volume.articles:
        if article.slug == article_slug:
            return volume, article
    return volume, None


def get_archive_categories():
    from .models import VolumeArticle

    categories = {}
    for category, label in VolumeArticle.CATEGORY_CHOICES:
        count = VolumeArticle.objects.filter(category=category).count()
        if count:
            categories[label] = count
    return [{'name': name, 'count': count} for name, count in categories.items()]


def get_popular_articles(limit=10):
    from .models import VolumeArticle

    items = []
    for article in VolumeArticle.objects.select_related('volume').order_by('-views_count')[:limit]:
        items.append(
            SimpleNamespace(
                title=article.title,
                authors=article.authors,
                date=_format_date(article.published_date),
            )
        )
    return items


def get_site_stats():
    from .models import Article, Author, Volume

    return {
        'published_articles': Article.objects.filter(status__in=['approved', 'published']).count(),
        'authors_count': Author.objects.count(),
        'issues_count': Volume.objects.filter(status='published').count(),
    }

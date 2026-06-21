"""Public sahifa viewlari — barcha ma'lumotlar PostgreSQL bazasidan."""

from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .i18n import LANGUAGE_SESSION_KEY, SUPPORTED_LANGUAGES
from .presenters import (
    find_volume_article,
    get_archive_categories,
    get_latest_home_articles,
    get_popular_articles,
    get_published_volumes,
    get_volume_by_slug,
    present_announcement,
    present_news,
)


def index(request):
    from .models import Announcement, News

    latest_news = [
        present_news(item)
        for item in News.objects.filter(is_active=True).order_by('-published_date')[:3]
    ]
    featured = (
        Announcement.objects.filter(is_active=True)
        .order_by('-published_date')
        .first()
    )
    featured_announcement = present_announcement(featured) if featured else None

    from .models import EditorialMember

    editorial_preview = EditorialMember.objects.filter(is_active=True).order_by('full_name')[:3]

    return render(request, 'index.html', {
        'latest_news': latest_news,
        'featured_announcement': featured_announcement,
        'editorial_preview': editorial_preview,
        'latest_articles': get_latest_home_articles(3),
    })


def haqida(request):
    return render(request, 'haqida.html')


def aloqa(request):
    msg = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            try:
                body_text = (
                    f"Ism: {name}\nEmail: {email}\nTelefon: {phone}\n"
                    f"Mavzu: {subject}\n\nXabar:\n{message}"
                )
                body_html = f"""
<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px'>
<h2 style='color:#02AB6F'>Yangi xabar - Aloqa formasi</h2>
<p><strong>Ism:</strong> {name}</p>
<p><strong>Email:</strong> {email}</p>
<p><strong>Telefon:</strong> {phone}</p>
<p><strong>Mavzu:</strong> {subject}</p>
<p><strong>Xabar:</strong><br>{message}</p>
</div>"""
                em = EmailMultiAlternatives(
                    subject=f"Aloqa formasi: {subject or 'Yangi xabar'} ({name})",
                    body=body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.CONTACT_EMAIL],
                    reply_to=[email],
                )
                em.attach_alternative(body_html, 'text/html')
                em.send()
                msg = ('success', 'Xabaringiz muvaffaqiyatli yuborildi! Tez orada javob beramiz.')
            except Exception as exc:
                import logging
                logging.getLogger(__name__).error('Aloqa email xatosi: %s', exc)
                msg = (
                    'error',
                    'Xabar yuborishda xatolik. Iltimos, bevosita '
                    f'<a href="mailto:{settings.CONTACT_EMAIL}">{settings.CONTACT_EMAIL}</a> ga yozing.',
                )
        else:
            msg = ('error', "Iltimos, barcha majburiy maydonlarni to'ldiring.")
    return render(request, 'aloqa.html', {'msg': msg})


def _validate_manuscript(upload):
    if not upload:
        return False, 'Fayl yuklang.'
    max_size = 10 * 1024 * 1024
    if upload.size > max_size:
        return False, 'Fayl hajmi 10MB dan oshmasligi kerak.'
    ext = Path(upload.name).suffix.lower()
    if ext != '.pdf':
        return False, 'Faqat PDF format qabul qilinadi.'
    return True, ''


def maqola_berish(request):
    from .models import Article, Author, Subscriber

    if request.method == 'POST':
        title = request.POST.get('article_title', '').strip()
        category = request.POST.get('category', '').strip()
        author_name = request.POST.get('author_name', '').strip()
        author_email = request.POST.get('email', '').strip()
        author_phone = request.POST.get('phone', '').strip()
        author_workplace = request.POST.get('organization', '').strip()
        author_position = request.POST.get('position', '').strip()
        author_degree = request.POST.get('degree', '')
        abstract = request.POST.get('abstract', '').strip()
        keywords = request.POST.get('keywords', '').strip()
        author_orcid = request.POST.get('orcid', '').strip()
        co_authors = request.POST.get('co_authors', '').strip()
        pdf_file = request.FILES.get('article_file')
        additional_files = request.FILES.get('additional_files')

        required = [title, category, author_name, author_email, author_phone, author_workplace, pdf_file]
        if not all(required):
            messages.error(request, "Majburiy maydonlarni to'ldiring va maqola faylini yuklang.")
            return redirect('maqola_berish')

        ok, err = _validate_manuscript(pdf_file)
        if not ok:
            messages.error(request, err)
            return redirect('maqola_berish')

        degree_label = Article.DEGREE_LABELS.get(author_degree, author_degree)

        author, created = Author.objects.get_or_create(
            full_name=author_name,
            email=author_email,
            phone=author_phone,
            defaults={
                'workplace': author_workplace,
                'academic_degree': degree_label,
            },
        )
        if not created:
            author.workplace = author_workplace
            author.academic_degree = degree_label
            author.save()

        article = Article.objects.create(
            author=author,
            title=title,
            category=category,
            author_name=author_name,
            author_email=author_email,
            author_phone=author_phone,
            author_workplace=author_workplace,
            author_position=author_position,
            author_degree=degree_label,
            author_orcid=author_orcid,
            co_authors=co_authors,
            abstract=abstract,
            keywords=keywords,
            pdf_file=pdf_file,
            additional_files=additional_files,
            status='pending',
            payment_status='pending',
        )
        author.update_statistics()

        Subscriber.objects.update_or_create(
            email=author_email,
            defaults={'full_name': author_name, 'source': 'article', 'is_active': True},
        )

        try:
            admin_body = (
                f"Yangi maqola yuborildi\n\n"
                f"ID: {article.id}\nSarlavha: {title}\nMuallif: {author_name}\n"
                f"Email: {author_email}\nTelefon: {author_phone}\n"
            )
            EmailMultiAlternatives(
                subject=f'Yangi maqola: {title}',
                body=admin_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
            ).send()
        except Exception:
            pass

        return render(request, 'maqola-success.html', {
            'article': article,
            'category_label': dict(Article.CATEGORY_CHOICES).get(category, category),
        })

    from .models import Article as ArticleModel
    return render(request, 'maqola-berish.html', {
        'categories': ArticleModel.CATEGORY_CHOICES,
    })


def tahrir_hayati(request):
    from .models import EditorialMember

    members = EditorialMember.objects.filter(is_active=True).order_by('full_name')
    return render(request, 'tahrir-hayati.html', {'members': members})


def jurnal_talablari(request):
    return render(request, 'jurnal-talablari.html')


def meyoriy_hujjatlar(request):
    from .models import RegulatoryDocument

    documents = RegulatoryDocument.objects.filter(is_active=True).order_by('-uploaded_at')
    return render(request, 'meyoriy-hujjatlar.html', {'documents': documents})


def arxiv(request):
    return render(request, 'arxiv.html', {
        'archive_volumes': get_published_volumes(),
    })


def arxiv_detail(request, slug):
    volume = get_volume_by_slug(slug)
    if not volume:
        raise Http404('Arxiv topilmadi')
    volume.obj.views_count = (volume.obj.views_count or 0) + 1
    volume.obj.save(update_fields=['views_count'])
    return render(request, 'arxiv-detail.html', {
        'volume': volume,
        'categories': get_archive_categories(),
        'popular_articles': get_popular_articles(),
    })


def arxiv_article_detail(request, volume_slug, article_slug):
    volume, article = find_volume_article(volume_slug, article_slug)
    if not volume or not article:
        raise Http404('Maqola topilmadi')
    if article.source == 'manual':
        article.obj.views_count = (article.obj.views_count or 0) + 1
        article.obj.save(update_fields=['views_count'])
    return render(request, 'arxiv-article-detail.html', {
        'volume': volume,
        'article': article,
    })


def arxiv_article_pdf_redirect(request, volume_slug, article_slug):
    volume, article = find_volume_article(volume_slug, article_slug)
    if not volume or not article or article.pdf_url == '#':
        raise Http404('PDF topilmadi')
    return redirect(article.pdf_url)


def arxiv_article_download(request, volume_slug, article_slug):
    volume, article = find_volume_article(volume_slug, article_slug)
    if not volume or not article:
        raise Http404('Maqola topilmadi')
    obj = article.obj
    if article.source == 'submitted' and obj.personal_pdf:
        file_obj = obj.personal_pdf
        filename = f'maqola_{obj.pk}.pdf'
    else:
        file_obj = obj.pdf_file
        filename = Path(file_obj.name).name if file_obj else ''
    if not file_obj:
        raise Http404('PDF fayl topilmadi')
    if article.source == 'submitted':
        obj.downloads_count = (obj.downloads_count or 0) + 1
        obj.save(update_fields=['downloads_count'])
    return FileResponse(
        file_obj.open('rb'),
        as_attachment=True,
        filename=filename,
        content_type='application/pdf',
    )


def set_language(request, lang_code):
    if lang_code in SUPPORTED_LANGUAGES:
        request.session[LANGUAGE_SESSION_KEY] = lang_code
        request.session.modified = True
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(reverse('index'))


def yangiliklar(request):
    from .models import News

    news_qs = News.objects.filter(is_active=True).order_by('-published_date')
    news_items = [present_news(item) for item in news_qs]
    categories = {}
    for item in news_qs:
        categories[item.category] = categories.get(item.category, 0) + 1

    return render(request, 'yangiliklar.html', {
        'news_items': news_items,
        'categories': categories,
        'total_news': news_qs.count(),
        'popular_articles': get_popular_articles(),
    })


def yangilik_detail(request, slug):
    from .models import News

    news_obj = get_object_or_404(News, slug=slug, is_active=True)
    news_obj.views += 1
    news_obj.save(update_fields=['views'])
    news = present_news(news_obj)
    related_news = [
        present_news(item)
        for item in News.objects.filter(is_active=True).exclude(pk=news_obj.pk).order_by('-published_date')[:3]
    ]
    return render(request, 'yangilik-detail.html', {
        'news': news,
        'related_news': related_news,
    })


def elonlar(request):
    from .models import Announcement

    announcements_qs = Announcement.objects.filter(is_active=True).order_by('-published_date')
    announcements = [present_announcement(item) for item in announcements_qs]
    priority_groups = {'yuqori': [], 'orta': [], 'past': []}
    for item in announcements:
        bucket = item.priority if item.priority in priority_groups else 'orta'
        priority_groups[bucket].append(item)

    categories = {}
    for item in announcements_qs:
        label = item.get_category_display()
        categories[label] = categories.get(label, 0) + 1

    return render(request, 'elonlar.html', {
        'announcements': announcements,
        'priority_groups': priority_groups,
        'categories': categories,
        'total_announcements': announcements_qs.count(),
    })


def elon_detail(request, slug):
    from .models import Announcement

    ann_obj = get_object_or_404(Announcement, slug=slug, is_active=True)
    announcement = present_announcement(ann_obj)
    related_announcements = [
        present_announcement(item)
        for item in Announcement.objects.filter(is_active=True).exclude(pk=ann_obj.pk).order_by('-published_date')[:3]
    ]
    return render(request, 'elon-detail.html', {
        'announcement': announcement,
        'related_announcements': related_announcements,
    })


def qidiruv(request):
    from .models import Article, News, VolumeArticle

    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', 'all')
    article_results = []
    news_results = []

    if query:
        if filter_type in ('title', 'all'):
            for item in VolumeArticle.objects.filter(title__icontains=query).select_related('volume')[:20]:
                if item.volume and item.volume.status == 'published':
                    article_results.append({
                        'title': item.title,
                        'authors': item.authors,
                        'url': reverse('arxiv_article_detail', args=[item.volume.slug, item.slug]),
                    })
            for item in Article.objects.filter(title__icontains=query, status__in=['approved', 'published'])[:20]:
                if item.volume and item.volume.status == 'published':
                    from django.utils.text import slugify
                    slug = slugify(item.title) or f'maqola-{item.pk}'
                    article_results.append({
                        'title': item.title,
                        'authors': item.author_name,
                        'url': reverse('arxiv_article_detail', args=[item.volume.slug, slug]),
                    })
        if filter_type in ('author', 'all'):
            for item in VolumeArticle.objects.filter(authors__icontains=query).select_related('volume')[:20]:
                if item.volume and item.volume.status == 'published':
                    article_results.append({
                        'title': item.title,
                        'authors': item.authors,
                        'url': reverse('arxiv_article_detail', args=[item.volume.slug, item.slug]),
                    })
        if filter_type in ('keywords', 'all'):
            for item in VolumeArticle.objects.filter(
                Q(keywords__icontains=query) | Q(abstract__icontains=query),
            ).select_related('volume')[:20]:
                if item.volume and item.volume.status == 'published':
                    article_results.append({
                        'title': item.title,
                        'authors': item.authors,
                        'url': reverse('arxiv_article_detail', args=[item.volume.slug, item.slug]),
                    })
        if filter_type == 'all':
            news_results = list(
                News.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query),
                    is_active=True,
                )[:10]
            )

        seen = set()
        unique_articles = []
        for item in article_results:
            key = item['url']
            if key not in seen:
                seen.add(key)
                unique_articles.append(item)
        article_results = unique_articles

    return render(request, 'qidiruv.html', {
        'query': query,
        'filter_type': filter_type,
        'article_results': article_results,
        'news_results': news_results,
        'results_total': len(article_results) + len(news_results),
    })


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def sitemap_xml(request):
    from .models import Announcement, News, Volume

    urls = [request.build_absolute_uri(reverse('index'))]
    for item in News.objects.filter(is_active=True):
        urls.append(request.build_absolute_uri(reverse('yangilik_detail', args=[item.slug])))
    for item in Announcement.objects.filter(is_active=True):
        urls.append(request.build_absolute_uri(reverse('elon_detail', args=[item.slug])))
    for item in Volume.objects.filter(status='published'):
        urls.append(request.build_absolute_uri(reverse('arxiv_detail', args=[item.slug])))

    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        body.append(f'  <url><loc>{url}</loc></url>')
    body.append('</urlset>')
    return HttpResponse('\n'.join(body), content_type='application/xml')


@require_POST
def subscribe(request):
    from .models import Subscriber

    full_name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').strip()
    if not full_name or not email:
        return JsonResponse({'ok': False, 'msg': "FIO va Email to'ldirish shart!"}, status=400)

    sub, created = Subscriber.objects.get_or_create(
        email=email,
        defaults={'full_name': full_name, 'source': 'newsletter', 'is_active': True},
    )
    if not created:
        sub.full_name = full_name
        sub.is_active = True
        sub.save()
        msg = "Siz allaqachon obunachisiz! Ma'lumotlaringiz yangilandi."
    else:
        msg = 'Obuna muvaffaqiyatli amalga oshirildi!'

    return JsonResponse({'ok': True, 'msg': msg})


def _file_download_response(file_field, filename=None):
    if not file_field:
        raise Http404('Fayl topilmadi')
    name = filename or Path(file_field.name).name
    return FileResponse(
        file_field.open('rb'),
        as_attachment=True,
        filename=name,
        content_type='application/pdf',
    )


def volume_pdf_download(request, slug):
    from .models import Volume

    volume = get_object_or_404(Volume, slug=slug)
    if not volume.pdf_file:
        raise Http404('Tom PDF hali tayyor emas')
    return _file_download_response(volume.pdf_file, f'tom_{volume.slug}.pdf')


def article_certificate_download(request, slug, article_id):
    from .models import Article

    article = get_object_or_404(Article, pk=article_id, volume__slug=slug, status='published')
    if not article.certificate_pdf:
        raise Http404('Sertifikat hali tayyor emas')
    return _file_download_response(article.certificate_pdf, f'sertifikat_{article.pk}.pdf')


def volume_detail_redirect(request, slug):
    """Tom sahifasi o'rniga arxiv tom sahifasiga yo'naltirish."""
    return redirect('arxiv_detail', slug=slug)

"""Admin va taqrizchi viewlari."""

import datetime
import os
import uuid
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from .pdf.generator import publish_article_to_volume
from .workflow import can_assign_reviewer, can_confirm_payment, can_send_payment, get_review, workflow_step_label


@staff_member_required
def admin_foydalanuvchilar(request):
    from .models import Author

    authors = Author.objects.annotate(
        total=Count('articles'),
        tasdiqlangan=Count('articles', filter=Q(articles__status='approved')),
        rad_etilgan=Count('articles', filter=Q(articles__status='rejected')),
        kutilmoqda=Count('articles', filter=Q(articles__status='pending')),
    ).order_by('-kutilmoqda', '-last_submission')

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    if search_query:
        authors = authors.filter(
            Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(workplace__icontains=search_query)
        )
    if status_filter == 'pending':
        authors = authors.filter(kutilmoqda__gt=0)
    elif status_filter == 'approved':
        authors = authors.filter(tasdiqlangan__gt=0)
    elif status_filter == 'rejected':
        authors = authors.filter(rad_etilgan__gt=0)

    return render(request, 'admin/foydalanuvchilar.html', {
        'authors': authors,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_authors': authors.count(),
    })


@staff_member_required
def admin_foydalanuvchi_detail(request, author_id):
    from .models import Article, Author, Reviewer, Volume

    author = get_object_or_404(Author, pk=author_id)
    all_articles = Article.objects.filter(author=author).order_by('title', '-submitted_at')

    grouped = {}
    for article in all_articles:
        key = article.title.strip().lower()
        grouped.setdefault(key, []).append(article)

    article_groups = []
    for articles in grouped.values():
        latest = articles[0]
        article_groups.append({
            'latest': latest,
            'history': articles[1:],
            'count': len(articles),
            'step': workflow_step_label(latest),
            'show_send_payment': can_send_payment(latest),
            'show_confirm_payment': can_confirm_payment(latest),
            'download_slug': slugify(latest.title) or f'maqola-{latest.pk}',
        })

    def sort_key(group):
        order = {'pending': 0, 'approved': 1, 'rejected': 2}
        return order.get(group['latest'].status, 3)

    article_groups.sort(key=sort_key)

    return render(request, 'admin/foydalanuvchi_detail.html', {
        'author': author,
        'article_groups': article_groups,
        'total': all_articles.count(),
        'all_reviewers': Reviewer.objects.all(),
        'active_volumes': Volume.objects.filter(status='active').order_by('-year', '-volume_number'),
    })


@staff_member_required
def admin_article_approve(request, article_id):
    """Eski URL — endi to'lov tasdiqlash va tomga qo'shish."""
    return admin_article_confirm_payment(request, article_id)


@staff_member_required
def admin_article_confirm_payment(request, article_id):
    """To'lovni tasdiqlash, tomga qo'shish va PDF generatsiya."""
    from .models import Article, Volume

    article = get_object_or_404(Article, pk=article_id)
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))

    if not can_confirm_payment(article):
        messages.error(
            request,
            'Avval taqrizchi tasdiqlashi va to\'lov linki yuborilishi kerak.',
        )
        return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))

    volume = None
    volume_id = request.POST.get('volume_id')
    if volume_id and volume_id != '0':
        try:
            volume = Volume.objects.get(pk=volume_id, status='active')
        except Volume.DoesNotExist:
            pass

    article.payment_status = 'paid'
    article.payment_date = timezone.now()
    article.save(update_fields=['payment_status', 'payment_date'])

    try:
        publish_article_to_volume(article, volume=volume)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))

    try:
        html = f"""
        <html><body style="font-family:Arial,sans-serif">
        <p>Hurmatli <strong>{article.author_name}</strong>,</p>
        <p>"{article.title}" maqolangiz to'lov tasdiqlandi va jurnal tomiga qo'shildi.</p>
        <p>Maqola va sertifikatni arxiv bo'limidan yuklab olishingiz mumkin.</p>
        <p>{settings.CONTACT_EMAIL}</p>
        </body></html>"""
        email = EmailMultiAlternatives(
            subject=f"Maqolangiz nashr etildi - {article.title}",
            body=f"Maqolangiz nashr etildi: {article.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[article.author_email],
        )
        email.attach_alternative(html, 'text/html')
        email.send()
    except Exception as exc:
        print(f'Email xatolik: {exc}')

    vol_title = article.volume.title if article.volume else ''
    messages.success(
        request,
        f'✅ To\'lov tasdiqlandi, "{vol_title}" tomiga qo\'shildi. PDF va sertifikat yaratildi!',
    )
    return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))


@staff_member_required
def admin_article_reject(request, article_id):
    from .models import Article

    article = get_object_or_404(Article, pk=article_id)
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))

    reason = request.POST.get('rejection_reason', '').strip()
    reviewer_file_path = request.POST.get('reviewer_file_path', '').strip()

    article.status = 'rejected'
    article.rejection_reason = reason
    article.rejection_date = timezone.now()
    article.rejection_notified = True
    article.save()
    if article.author:
        article.author.update_statistics()

    try:
        html = f"""
        <html><body style="font-family:Arial,sans-serif">
        <p>Hurmatli <strong>{article.author_name}</strong>,</p>
        <p>"{article.title}" maqolangiz rad etildi.</p>
        <p><strong>Sabab:</strong> {reason}</p>
        <p>Savollar: {settings.CONTACT_EMAIL}</p>
        </body></html>"""
        email = EmailMultiAlternatives(
            subject=f"Maqola haqida xabar - {article.title}",
            body=f"Rad etildi. Sabab: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[article.author_email],
        )
        email.attach_alternative(html, 'text/html')
        if article.pdf_file:
            email.attach_file(article.pdf_file.path)
        if reviewer_file_path:
            full_path = os.path.join(settings.MEDIA_ROOT, reviewer_file_path)
            if os.path.exists(full_path):
                email.attach_file(full_path)
        email.send()
    except Exception as exc:
        print(f'Email xatolik: {exc}')

    messages.success(request, '❌ Maqola rad etildi va muallifga xabar yuborildi!')
    return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))


@staff_member_required
def admin_article_send_payment(request, article_id):
    from .models import Article

    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', '/'))

    article = get_object_or_404(Article, pk=article_id)

    if not can_send_payment(article):
        messages.error(request, 'To\'lov linki faqat taqrizchi tasdiqlagandan keyin yuboriladi.')
        return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))

    article.payment_link_sent = True
    article.payment_link_sent_at = timezone.now()
    article.payment_link_sent_count = (article.payment_link_sent_count or 0) + 1
    article.save()

    try:
        html = f"""
        <html><body style="font-family:Arial,sans-serif">
        <p>Hurmatli <strong>{article.author_name}</strong>,</p>
        <p>"{article.title}" maqolangiz nashr uchun to'lov talab qiladi.</p>
        <p>Telegram: @XURSHID_HAMD11 | Tel: +998 97 736 20 11</p>
        <p>Email: {settings.CONTACT_EMAIL}</p>
        </body></html>"""
        email = EmailMultiAlternatives(
            subject=f"To'lov haqida ma'lumot - {article.title}",
            body=f"To'lov haqida: {article.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[article.author_email],
        )
        email.attach_alternative(html, 'text/html')
        email.send()
    except Exception as exc:
        print(f'Email xatolik: {exc}')

    messages.success(
        request,
        f"💰 To'lov ko'rsatmalari yuborildi! (Jami: {article.payment_link_sent_count} marta)",
    )
    return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))


@staff_member_required
def admin_taqrizchilar(request):
    from .models import Reviewer

    msg = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            full_name = request.POST.get('full_name', '').strip()
            position = request.POST.get('position', '').strip()
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            specialization = request.POST.get('specialization', 'chemistry')
            photo = request.FILES.get('photo')
            if not full_name or not username or not password:
                msg = ('error', 'F.I.O, username va parol majburiy!')
            elif User.objects.filter(username=username).exists():
                msg = ('error', f'"{username}" username allaqachon mavjud!')
            else:
                user = User.objects.create_user(username=username, password=password)
                reviewer = Reviewer.objects.create(
                    user=user, full_name=full_name, position=position, specialization=specialization,
                )
                if photo:
                    reviewer.photo = photo
                    reviewer.save()
                msg = ('success', f'✅ Taqrizchi "{full_name}" yaratildi!')
        elif action == 'edit':
            reviewer_id = request.POST.get('reviewer_id')
            try:
                reviewer = Reviewer.objects.select_related('user').get(pk=reviewer_id)
                reviewer.full_name = request.POST.get('full_name', '').strip()
                reviewer.position = request.POST.get('position', '').strip()
                reviewer.specialization = request.POST.get('specialization', 'chemistry')
                if request.FILES.get('photo'):
                    reviewer.photo = request.FILES['photo']
                reviewer.save()
                username = request.POST.get('username', '').strip()
                if username and username != reviewer.user.username:
                    reviewer.user.username = username
                    reviewer.user.save()
                new_password = request.POST.get('new_password', '').strip()
                if new_password:
                    reviewer.user.set_password(new_password)
                    reviewer.user.save()
                msg = ('success', f'✅ "{reviewer.full_name}" yangilandi')
            except Reviewer.DoesNotExist:
                msg = ('error', 'Taqrizchi topilmadi')
        elif action == 'delete':
            try:
                Reviewer.objects.get(pk=request.POST.get('reviewer_id')).user.delete()
                msg = ('success', '🗑 Taqrizchi o\'chirildi')
            except Reviewer.DoesNotExist:
                msg = ('error', 'Taqrizchi topilmadi')

    reviewers = Reviewer.objects.select_related('user').prefetch_related('reviews').all()
    return render(request, 'admin/taqrizchilar.html', {'reviewers': reviewers, 'msg': msg})


@staff_member_required
def admin_article_assign_reviewer(request, article_id):
    from .models import Article, ArticleReview, Reviewer

    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        reviewer_id = request.POST.get('reviewer_id')
        if reviewer_id in ('0', '', None):
            ArticleReview.objects.filter(article=article).delete()
            messages.success(request, '✅ Taqrizchi biriktirishi o\'chirildi')
        else:
            try:
                reviewer = Reviewer.objects.get(pk=reviewer_id)
                review, created = ArticleReview.objects.get_or_create(
                    article=article, defaults={'reviewer': reviewer},
                )
                if not created:
                    review.reviewer = reviewer
                    review.status = 'pending'
                    review.rejection_reason = ''
                    review.rejection_file = None
                    review.reviewed_at = None
                    review.save()
                messages.success(request, f'✅ Maqola "{reviewer.full_name}" ga biriktirildi')
            except Reviewer.DoesNotExist:
                messages.error(request, 'Taqrizchi topilmadi')
    return redirect(request.META.get('HTTP_REFERER', f'/admin-panel/foydalanuvchi/{article.author_id}/'))


def reviewer_login(request):
    from django.contrib.auth import authenticate, login

    if request.user.is_authenticated and hasattr(request.user, 'reviewer_profile'):
        return redirect('reviewer_profil')

    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', '').strip(),
            password=request.POST.get('password', '').strip(),
        )
        if user and hasattr(user, 'reviewer_profile'):
            login(request, user)
            return redirect('reviewer_profil')
        error = 'Login yoki parol noto\'g\'ri, yoki siz taqrizchi emassiz'
    return render(request, 'taqrizchi/login.html', {'error': error})


def reviewer_logout(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect('reviewer_login')


def _reviewer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'reviewer_profile'):
            return redirect('reviewer_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@_reviewer_required
def reviewer_profil(request):
    reviewer = request.user.reviewer_profile
    return render(request, 'taqrizchi/profil.html', {
        'reviewer': reviewer,
        'pending_reviews': reviewer.reviews.filter(status='pending').select_related('article', 'article__author'),
        'archive_reviews': reviewer.reviews.exclude(status='pending').select_related(
            'article', 'article__author',
        ).order_by('-reviewed_at'),
    })


@_reviewer_required
def reviewer_article_detail(request, review_id):
    from .models import ArticleReview

    review = get_object_or_404(ArticleReview, pk=review_id, reviewer=request.user.reviewer_profile)
    return render(request, 'taqrizchi/maqola_detail.html', {
        'reviewer': request.user.reviewer_profile,
        'review': review,
        'article': review.article,
    })


@_reviewer_required
def reviewer_article_approve(request, review_id):
    from .models import ArticleReview

    review = get_object_or_404(ArticleReview, pk=review_id, reviewer=request.user.reviewer_profile)
    if review.status == 'pending':
        review.status = 'approved'
        review.reviewed_at = timezone.now()
        review.save()
        messages.success(request, '✅ Maqola tasdiqlandi! Admin xabardor bo\'ldi.')
    return redirect('reviewer_profil')


@_reviewer_required
def reviewer_article_reject(request, review_id):
    from .models import ArticleReview

    review = get_object_or_404(ArticleReview, pk=review_id, reviewer=request.user.reviewer_profile)
    if request.method == 'POST' and review.status == 'pending':
        review.status = 'rejected'
        review.rejection_reason = request.POST.get('rejection_reason', '').strip()
        review.reviewed_at = timezone.now()
        review.save()
        messages.success(request, '❌ Maqola rad etildi. Admin sahifada ko\'rsatiladi.')
    return redirect('reviewer_profil')


@staff_member_required
def admin_tomlar(request):
    from .models import Volume

    msg = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            title = request.POST.get('title', '').strip()
            if not title:
                msg = ('error', 'Tom nomi majburiy!')
            else:
                base_slug = slugify(title) or f'tom-{uuid.uuid4().hex[:6]}'
                slug = base_slug
                counter = 1
                while Volume.objects.filter(slug=slug).exists():
                    slug = f'{base_slug}-{counter}'
                    counter += 1
                vol = Volume.objects.create(
                    title=title,
                    slug=slug,
                    year=int(request.POST.get('year', timezone.now().year)),
                    volume_number=int(request.POST.get('volume_number', 1)),
                    issue_number=int(request.POST.get('issue_number', 1)),
                    max_articles=int(request.POST.get('max_articles', 10)),
                    status=request.POST.get('status', 'draft'),
                    description=request.POST.get('description', '').strip(),
                    subject=request.POST.get('subject', 'mixed'),
                )
                if request.FILES.get('cover_image'):
                    vol.cover_image = request.FILES['cover_image']
                    vol.save()
                msg = ('success', f'✅ "{title}" tomi yaratildi!')
        elif action == 'delete':
            try:
                vol = Volume.objects.get(pk=request.POST.get('volume_id'))
                name = vol.title
                vol.volume_articles.update(volume=None)
                vol.delete()
                msg = ('success', f'🗑 "{name}" tomi o\'chirildi')
            except Volume.DoesNotExist:
                msg = ('error', 'Tom topilmadi')
        elif action == 'edit':
            try:
                vol = Volume.objects.get(pk=request.POST.get('volume_id'))
                vol.title = request.POST.get('title', '').strip()
                vol.max_articles = int(request.POST.get('max_articles', 10))
                vol.status = request.POST.get('status', 'draft')
                vol.description = request.POST.get('description', '').strip()
                vol.subject = request.POST.get('subject', 'mixed')
                if request.POST.get('year'):
                    vol.year = int(request.POST['year'])
                if request.POST.get('volume_number'):
                    vol.volume_number = int(request.POST['volume_number'])
                if request.POST.get('issue_number'):
                    vol.issue_number = int(request.POST['issue_number'])
                if request.FILES.get('cover_image'):
                    vol.cover_image = request.FILES['cover_image']
                if request.FILES.get('pdf_file'):
                    vol.pdf_file = request.FILES['pdf_file']
                    if vol.status == 'published' and not vol.published_at:
                        vol.published_at = timezone.now()
                vol.save()
                msg = ('success', f'✅ "{vol.title}" tomi yangilandi!')
            except Volume.DoesNotExist:
                msg = ('error', 'Tom topilmadi')

    return render(request, 'admin/tomlar.html', {
        'volumes': Volume.objects.prefetch_related('volume_articles').all(),
        'msg': msg,
    })


@staff_member_required
def admin_tom_detail(request, volume_id):
    from .models import Article, Volume, VolumeArticle

    volume = get_object_or_404(Volume, pk=volume_id)
    msg = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'remove_article':
            try:
                art = Article.objects.get(pk=request.POST.get('article_id'), volume=volume)
                art.volume = None
                art.save()
                msg = ('success', '✅ Maqola tomdan olib tashlandi')
            except Article.DoesNotExist:
                msg = ('error', 'Maqola topilmadi')
        elif action == 'upload_pdf':
            pdf = request.FILES.get('pdf_file')
            if pdf:
                volume.pdf_file = pdf
                volume.save()
                msg = ('success', '✅ PDF muvaffaqiyatli yuklandi')
            else:
                msg = ('error', 'Fayl tanlanmadi')
        elif action == 'add_manual_article':
            title = request.POST.get('ma_title', '').strip()
            authors = request.POST.get('ma_authors', '').strip()
            if not title or not authors:
                msg = ('error', 'Maqola mavzusi va avtorlari majburiy!')
            elif volume.is_full:
                msg = ('error', f'❌ Tom to\'lgan! Limit: {volume.max_articles}')
            else:
                parsed_date = None
                pub_date = request.POST.get('ma_date', '').strip()
                if pub_date:
                    try:
                        parsed_date = datetime.date.fromisoformat(pub_date)
                    except ValueError:
                        pass
                ma = VolumeArticle.objects.create(
                    volume=volume,
                    category=request.POST.get('ma_category', 'chemistry'),
                    title=title,
                    authors=authors,
                    published_date=parsed_date,
                    abstract=request.POST.get('ma_abstract', '').strip(),
                    keywords=request.POST.get('ma_keywords', '').strip(),
                    references=request.POST.get('ma_references', '').strip(),
                    doi=request.POST.get('ma_doi', '').strip(),
                    pages=request.POST.get('ma_pages', '').strip(),
                )
                if request.FILES.get('ma_pdf'):
                    ma.pdf_file = request.FILES['ma_pdf']
                    ma.save()
                msg = ('success', f'✅ "{title}" maqolasi tomga qo\'shildi')
        elif action == 'edit_manual_article':
            try:
                ma = VolumeArticle.objects.get(pk=request.POST.get('ma_id'), volume=volume)
                ma.title = request.POST.get('ma_title', '').strip()
                ma.authors = request.POST.get('ma_authors', '').strip()
                ma.category = request.POST.get('ma_category', 'chemistry')
                ma.abstract = request.POST.get('ma_abstract', '').strip()
                ma.keywords = request.POST.get('ma_keywords', '').strip()
                ma.references = request.POST.get('ma_references', '').strip()
                ma.doi = request.POST.get('ma_doi', '').strip()
                ma.pages = request.POST.get('ma_pages', '').strip()
                pub_date = request.POST.get('ma_date', '').strip()
                if pub_date:
                    try:
                        ma.published_date = datetime.date.fromisoformat(pub_date)
                    except ValueError:
                        pass
                if request.FILES.get('ma_pdf'):
                    ma.pdf_file = request.FILES['ma_pdf']
                ma.save()
                msg = ('success', '✅ Maqola ma\'lumotlari yangilandi')
            except VolumeArticle.DoesNotExist:
                msg = ('error', 'Maqola topilmadi')
        elif action == 'remove_manual_article':
            try:
                VolumeArticle.objects.get(pk=request.POST.get('ma_id'), volume=volume).delete()
                msg = ('success', '🗑 Maqola o\'chirildi')
            except VolumeArticle.DoesNotExist:
                msg = ('error', 'Maqola topilmadi')

    return render(request, 'admin/tom_detail.html', {
        'volume': volume,
        'articles': volume.volume_articles.select_related('author').order_by('approved_at'),
        'manual_articles': volume.manual_articles.all(),
        'category_choices': VolumeArticle.CATEGORY_CHOICES,
        'msg': msg,
    })


@staff_member_required
def admin_obunachlar(request):
    from .models import Subscriber

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        try:
            Subscriber.objects.get(pk=request.POST.get('sub_id')).delete()
            messages.success(request, "Obunachi o'chirildi.")
        except Subscriber.DoesNotExist:
            pass
        return redirect('admin_obunachlar')

    q = request.GET.get('q', '').strip()
    qs = Subscriber.objects.all()
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(email__icontains=q))

    return render(request, 'admin/obunachlar.html', {
        'subscribers': qs,
        'total': Subscriber.objects.count(),
        'active': Subscriber.objects.filter(is_active=True).count(),
        'q': q,
    })

"""To'lov jarayoni — Click demo va kelajakdagi haqiqiy integratsiya."""

from __future__ import annotations

import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .workflow import can_confirm_payment


class PaymentError(Exception):
    """To'lovni yakunlab bo'lmagan holat."""


def default_payment_amount() -> Decimal:
    return Decimal(str(getattr(settings, 'DEFAULT_PAYMENT_AMOUNT', '500000')))


def create_payment_session(article, amount=None, base_url=''):
    """Yangi to'lov sessiyasi yaratadi va token qaytaradi."""
    from .models import ArticlePaymentSession

    if amount is None or amount <= 0:
        amount = article.payment_amount or default_payment_amount()
    else:
        amount = Decimal(str(amount))

    article.payment_amount = amount
    article.save(update_fields=['payment_amount'])

    session = ArticlePaymentSession.objects.create(
        article=article,
        token=secrets.token_urlsafe(32),
        amount=amount,
    )
    return session


def payment_page_url(session, request=None, base_url=''):
    path = reverse('payment_checkout', args=[session.token])
    if request is not None:
        return request.build_absolute_uri(path)
    site = (base_url or getattr(settings, 'SITE_URL', '')).rstrip('/')
    return f'{site}{path}'


def _notify_admin(subject, html_body):
    recipients = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', None) or [settings.CONTACT_EMAIL]
    recipients = [r for r in recipients if r]
    if not recipients:
        return
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_body, 'text/html')
        email.send()
    except Exception as exc:
        print(f'Admin email xatolik: {exc}')


def send_payment_link_email(article, payment_url):
    amount = article.payment_amount or default_payment_amount()
    amount_fmt = f'{amount:,.0f}'.replace(',', ' ')
    html = f"""
    <html><body style="font-family:Arial,sans-serif;line-height:1.6">
    <p>Hurmatli <strong>{article.author_name}</strong>,</p>
    <p>"{article.title}" maqolangiz nashr uchun to'lov talab qiladi.</p>
    <p><strong>To'lov summasi:</strong> {amount_fmt} so'm</p>
    <p style="margin:24px 0">
        <a href="{payment_url}" style="background:#02AB6F;color:white;padding:14px 28px;
        border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block">
            To'lov sahifasiga o'tish
        </a>
    </p>
    <p style="font-size:13px;color:#64748b">Yoki havolani nusxalang: {payment_url}</p>
    <p>Savollar: {settings.CONTACT_EMAIL}</p>
    </body></html>"""
    email = EmailMultiAlternatives(
        subject=f"To'lov — {article.title}",
        body=f"To'lov havolasi: {payment_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[article.author_email],
    )
    email.attach_alternative(html, 'text/html')
    email.send()


def send_payment_received_email(article):
    """To'lov qabul qilindi — nashr admin tom biriktirgach bo'ladi."""
    html = f"""
    <html><body style="font-family:Arial,sans-serif;line-height:1.6">
    <p>Hurmatli <strong>{article.author_name}</strong>,</p>
    <p>"{article.title}" maqolangiz uchun to'lov muvaffaqiyatli qabul qilindi.</p>
    <p>Tahririyat maqolani jurnal tomiga biriktirgach sizga alohida xabar yuboriladi.</p>
    <p>Savollar: {settings.CONTACT_EMAIL}</p>
    </body></html>"""
    email = EmailMultiAlternatives(
        subject=f"To'lov qabul qilindi — {article.title}",
        body=f"To'lovingiz qabul qilindi: {article.title}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[article.author_email],
    )
    email.attach_alternative(html, 'text/html')
    email.send()


def send_published_email(article):
    vol_title = article.volume.title if article.volume else ''
    html = f"""
    <html><body style="font-family:Arial,sans-serif">
    <p>Hurmatli <strong>{article.author_name}</strong>,</p>
    <p>"{article.title}" maqolangiz to'lov qabul qilindi va jurnal tomiga qo'shildi.</p>
    <p><strong>Tom:</strong> {vol_title}</p>
    <p>Maqola va sertifikatni arxiv bo'limidan yuklab olishingiz mumkin.</p>
    <p>{settings.CONTACT_EMAIL}</p>
    </body></html>"""
    email = EmailMultiAlternatives(
        subject=f"Maqolangiz nashr etildi — {article.title}",
        body=f"Maqolangiz nashr etildi: {article.title}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[article.author_email],
    )
    email.attach_alternative(html, 'text/html')
    email.send()


@transaction.atomic
def complete_article_payment(session, transaction_id='', click_payment_id=''):
    """To'lovni tasdiqlaydi — faqat paid belgilaydi, tom admin biriktiradi."""
    from .models import Article, ArticlePaymentSession

    session = ArticlePaymentSession.objects.select_for_update().get(pk=session.pk)
    article = Article.objects.select_for_update().get(pk=session.article_id)

    if article.payment_status == 'paid':
        if session.status != 'paid':
            session.status = 'paid'
            session.paid_at = article.payment_date or timezone.now()
            session.transaction_id = article.payment_transaction_id or transaction_id
            session.save(update_fields=['status', 'paid_at', 'transaction_id'])
        return article

    if not session.is_payable:
        raise PaymentError("Bu to'lov havolasi endi amal qilmaydi.")

    if not can_confirm_payment(article):
        raise PaymentError(
            "Maqola to'lov uchun tayyor emas. Taqrizchi tasdiqlashi va to'lov linki yuborilgan bo'lishi kerak."
        )

    txn = transaction_id or f'DEMO-{uuid.uuid4().hex[:12].upper()}'

    article.payment_status = 'paid'
    article.payment_date = timezone.now()
    article.payment_transaction_id = txn
    article.save(update_fields=['payment_status', 'payment_date', 'payment_transaction_id'])

    session.status = 'paid'
    session.paid_at = timezone.now()
    session.transaction_id = txn
    if click_payment_id:
        session.click_payment_id = click_payment_id
    session.save(update_fields=['status', 'paid_at', 'transaction_id', 'click_payment_id'])

    try:
        send_payment_received_email(article)
    except Exception as exc:
        print(f'Muallif email xatolik: {exc}')

    _notify_admin(
        f"To'lov qabul qilindi — {article.title}",
        f'<p><strong>{article.author_name}</strong> — "{article.title}" uchun to\'lov qabul qilindi.</p>'
        f'<p>Tranzaksiya: {txn}</p>'
        f'<p><strong>Keyingi qadam:</strong> Admin paneldan tomga biriktiring.</p>',
    )
    return article


def notify_reviewer_decision(review, decision):
    article = review.article
    reviewer = review.reviewer
    if decision == 'approved':
        subject = f'Taqrizchi tasdiqladi — {article.title}'
        body = (
            f'<p>Taqrizchi <strong>{reviewer.full_name}</strong> maqolani tasdiqladi.</p>'
            f'<p><strong>Maqola:</strong> {article.title}</p>'
            f'<p><strong>Muallif:</strong> {article.author_name}</p>'
            f'<p>Endi to\'lov linkini yuborishingiz mumkin.</p>'
        )
    else:
        reason = review.rejection_reason or '—'
        subject = f'Taqrizchi rad etdi — {article.title}'
        body = (
            f'<p>Taqrizchi <strong>{reviewer.full_name}</strong> maqolani rad etdi.</p>'
            f'<p><strong>Maqola:</strong> {article.title}</p>'
            f'<p><strong>Sabab:</strong> {reason}</p>'
        )
    _notify_admin(subject, body)

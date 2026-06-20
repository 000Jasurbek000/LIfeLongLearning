"""Maqola ishlab chiqish jarayoni (workflow) yordamchilari."""

from __future__ import annotations


def get_review(article):
    return article.reviews.select_related('reviewer').first()


def review_is_approved(article) -> bool:
    review = get_review(article)
    return review is not None and review.status == 'approved'


def review_is_rejected(article) -> bool:
    review = get_review(article)
    return review is not None and review.status == 'rejected'


def review_is_pending(article) -> bool:
    review = get_review(article)
    return review is not None and review.status == 'pending'


def has_reviewer(article) -> bool:
    return get_review(article) is not None


def can_send_payment(article) -> bool:
    """Taqrizchi tasdiqlagandan keyin to'lov yuborish mumkin."""
    return (
        article.status in ('pending', 'approved')
        and review_is_approved(article)
        and article.payment_status != 'paid'
    )


def can_confirm_payment(article) -> bool:
    """To'lov tasdiqlash va tomga qo'shish."""
    return (
        review_is_approved(article)
        and article.payment_link_sent
        and article.payment_status != 'paid'
        and article.status != 'published'
    )


def can_assign_reviewer(article) -> bool:
    return article.status == 'pending' and not article.volume_id


def workflow_step_label(article) -> str:
    if article.status == 'published':
        return 'Nashr etilgan'
    if article.status == 'rejected':
        return 'Rad etilgan'
    if not has_reviewer(article):
        return '1. Taqrizchi biriktirish'
    if review_is_pending(article):
        return '2. Taqriz kutilmoqda'
    if review_is_rejected(article):
        return 'Taqrizchi rad etdi'
    if review_is_approved(article) and not article.payment_link_sent:
        return '3. To\'lov linki yuborish'
    if review_is_approved(article) and article.payment_link_sent and article.payment_status != 'paid':
        return '4. To\'lovni tasdiqlash va tomga qo\'shish'
    if article.payment_status == 'paid' and not article.volume_id:
        return 'Tomga biriktirish kutilmoqda'
    return 'Jarayonda'

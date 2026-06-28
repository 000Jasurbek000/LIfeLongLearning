"""To'lov sahifalari — Click demo integratsiyasi."""

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .models import ArticlePaymentSession
from .payment import PaymentError, complete_article_payment


def _get_session(token):
    return get_object_or_404(
        ArticlePaymentSession.objects.select_related('article', 'article__author'),
        token=token,
    )


def payment_checkout(request, token):
    """To'lov buyurtmasi — maqola va muallif ma'lumotlari."""
    session = _get_session(token)
    article = session.article

    if article.payment_status == 'paid':
        return render(request, 'payment/success.html', {
            'session': session,
            'article': article,
            'already_paid': True,
        })

    if not session.is_payable:
        return render(request, 'payment/error.html', {
            'session': session,
            'article': article,
            'message': "Bu to'lov havolasi muddati tugagan yoki bekor qilingan.",
        })

    return render(request, 'payment/checkout.html', {
        'session': session,
        'article': article,
        'site_name': settings.SITE_NAME,
        'click_demo': settings.CLICK_DEMO_MODE,
    })


def payment_click_demo(request, token):
    """Demo Click to'lov sahifasi."""
    session = _get_session(token)
    article = session.article

    if article.payment_status == 'paid':
        return redirect('payment_success', token=token)

    if not session.is_payable:
        return render(request, 'payment/error.html', {
            'session': session,
            'article': article,
            'message': "Bu to'lov havolasi endi amal qilmaydi.",
        })

    return render(request, 'payment/click_demo.html', {
        'session': session,
        'article': article,
        'merchant_name': settings.SITE_NAME,
        'click_merchant_id': settings.CLICK_MERCHANT_ID or 'DEMO',
    })


@require_POST
def payment_click_pay(request, token):
    """Demo: Click to'lovni tasdiqlash va avtomatik nashr."""
    session = _get_session(token)
    article = session.article

    if article.payment_status == 'paid':
        return redirect('payment_success', token=token)

    demo_txn = request.POST.get('demo_transaction_id', '').strip()

    try:
        complete_article_payment(
            session,
            transaction_id=demo_txn or '',
            click_payment_id=f'CLICK-DEMO-{session.pk}',
        )
    except PaymentError as exc:
        messages.error(request, str(exc))
        return redirect('payment_click_demo', token=token)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('payment_checkout', token=token)
    except Exception as exc:
        messages.error(request, f"To'lovni yakunlashda xatolik: {exc}")
        return redirect('payment_checkout', token=token)

    return redirect('payment_success', token=token)


def payment_success(request, token):
    session = _get_session(token)
    return render(request, 'payment/success.html', {
        'session': session,
        'article': session.article,
        'already_paid': False,
    })


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def payment_click_callback(request):
    """
    Kelajakdagi haqiqiy Click webhook.
    Hozircha demo rejimda faqat holat haqida xabar qaytaradi.
    """
    if settings.CLICK_DEMO_MODE:
        return JsonResponse({
            'error': 0,
            'error_note': 'Demo rejim — haqiqiy Click callback keyinroq ulanadi.',
        })

  # Haqiqiy integratsiya shu yerda bo'ladi (CLICK_MERCHANT_ID, imzo tekshiruvi)
    return JsonResponse({'error': -1, 'error_note': 'Click integratsiyasi sozlanmagan'})

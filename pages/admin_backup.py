from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms
from .models import Article, EditorialMember, RegulatoryDocument, News, Announcement, Author
import os


# Article va Author admin paneldan olib tashlandi


# @admin.register(Author)
# class AuthorAdmin(admin.ModelAdmin):
#     pass


# @admin.register(Article)
# class ArticleAdmin(admin.ModelAdmin):
    """Zamonaviy va tushunarli maqola admin paneli"""
    
    # Ro'yxat ko'rinishi
    list_display = [
        'author_name_display',
        'category',
        'author_phone_display',
        'colored_status',
        'colored_payment_status',
        'payment_link_status',
        'submitted_date',
        'action_buttons'
    ]
    
    list_filter = [
        'status',
        'category',
        'payment_status',
        'submitted_at',
        'approved_at',
    ]
    
    search_fields = [
        'title',
        'author_name',
        'author_email'
    ]
    
    readonly_fields = [
        'submitted_at',
        'updated_at',
        'approved_at',
        'published_at',
        'rejection_date',
        'pdf_preview',
        'author_contact_info'
    ]
    
    # Fieldsets - to'liq ma'lumotlar
    fieldsets = (
        ('📄 Maqola Ma\'lumotlari', {
            'fields': ('title', 'category', 'pdf_file', 'pdf_preview', 'additional_files')
        }),
        ('👤 Muallif Ma\'lumotlari', {
            'fields': ('author_name', 'author_email', 'author_phone', 'author_degree', 
                      'author_workplace', 'author_orcid', 'author_contact_info'),
            'classes': ('collapse',)
        }),
        ('💰 To\'lov Ma\'lumotlari', {
            'fields': ('payment_status', 'payment_amount', 'payment_date', 'payment_transaction_id')
        }),
        ('✅ Holat va Tasdiqlash', {
            'fields': ('status', 'approved_at', 'published_at')
        }),
        ('❌ Bekor Qilish Ma\'lumotlari', {
            'fields': ('rejection_reason', 'rejection_date', 'rejection_notified'),
            'classes': ('collapse',)
        }),
        ('📊 Statistika va Qo\'shimcha', {
            'fields': ('views_count', 'downloads_count', 'notes', 'submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        """Custom URL routelar"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:article_id>/view/', self.admin_site.admin_view(self.view_article_detail), name='pages_article_view'),
            path('<int:article_id>/approve/', self.admin_site.admin_view(self.approve_article_view), name='pages_article_approve'),
            path('<int:article_id>/reject/', self.admin_site.admin_view(self.reject_article_view), name='pages_article_reject'),
            path('<int:article_id>/send-payment-link/', self.admin_site.admin_view(self.send_payment_link_view), name='pages_article_send_payment_link'),
        ]
        return custom_urls + urls
    
    def view_article_detail(self, request, article_id):
        """Maqola ma'lumotlarini ko'rish sahifasi"""
        article = get_object_or_404(Article, pk=article_id)
        
        context = {
            'article': article,
            'title': f"Ko'rish - {article.title}",
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/pages/view_article.html', context)
    
    def approve_article_view(self, request, article_id):
        """Tasdiqlash"""
        article = get_object_or_404(Article, pk=article_id)
        
        # Tasdiqlash
        article.status = 'approved'
        article.approved_at = timezone.now()
        article.payment_status = 'paid'  # To'lov holati ham tasdiqlanadi
        article.payment_date = timezone.now()
        article.save()
        
        # Muallif statistikasini yangilash
        article.author.update_statistics()
        
        # Email yuborish
        self.send_approval_email(article)
        
        messages.success(request, f'✅ Maqola va to\'lov tasdiqlandi! Muallifga xabar yuborildi.')
        
        # Qaytish
        referer = request.META.get('HTTP_REFERER')
        if referer and 'view' in referer:
            return redirect('admin:pages_article_view', article_id=article_id)
        return redirect('admin:pages_article_changelist')
    
    def reject_article_view(self, request, article_id):
        """Bekor qilish sahifasi"""
        article = get_object_or_404(Article, pk=article_id)
        
        if request.method == 'POST':
            form = RejectArticleForm(request.POST, request.FILES)
            if form.is_valid():
                # Bekor qilish
                article.status = 'rejected'
                article.rejection_reason = form.cleaned_data['rejection_reason']
                article.rejection_date = timezone.now()
                article.save()
                
                # Muallif statistikasini yangilash
                article.author.update_statistics()
                
                # Email yuborish (fayl bilan)
                rejection_file = form.cleaned_data.get('rejection_file')
                self.send_rejection_email(article, rejection_file)
                article.rejection_notified = True
                article.save()
                
                messages.success(request, f'❌ Maqola bekor qilindi va muallifga xabar yuborildi!')
                
                # Qaytish
                referer = request.META.get('HTTP_REFERER')
                if referer and 'view' in referer:
                    return redirect('admin:pages_article_view', article_id=article.pk)
                return redirect('admin:pages_article_changelist')
        else:
            form = RejectArticleForm()
        
        context = {
            'article': article,
            'form': form,
            'title': f'Maqolani bekor qilish - {article.title}',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/pages/reject_article.html', context)
    
    def send_payment_link_view(self, request, article_id):
        """To'lov uchun link yuborish"""
        article = get_object_or_404(Article, pk=article_id)
        
        # To'lov emailini yuborish
        self.send_payment_email(article)
        
        # To'lov linki yuborilganligini belgilash
        article.payment_link_sent = True
        article.payment_link_sent_at = timezone.now()
        article.payment_link_sent_count += 1
        article.save()
        
        messages.success(request, f'💰 To\'lov ko\'rsatmalari muallifga yuborildi!')
        
        # Qaytish
        referer = request.META.get('HTTP_REFERER')
        if referer and 'view' in referer:
            return redirect('admin:pages_article_view', article_id=article_id)
        return redirect('admin:pages_article_changelist')
    
    # Guruhli actions
    actions = ['mark_as_paid']
    
    def author_name_display(self, obj):
        """Muallif FIO"""
        return format_html(
            '<div style="max-width: 240px; line-height: 1.4; font-size: 14px;" title="Maqola: {}">'
            '<strong style="color: #2c3e50;">{}</strong>'
            '</div>',
            obj.title,
            obj.author_name
        )
    author_name_display.short_description = 'Muallif FIO'
    
    def author_phone_display(self, obj):
        """Telefon raqam"""
        return format_html(
            '<div style="min-width: 120px; font-size: 14px;" title="{}">'
            '<strong style="color: #2c3e50;">{}</strong>'
            '</div>',
            obj.author_email,
            obj.author_phone
        )
    author_phone_display.short_description = 'Telefon'
    
    def colored_title(self, obj):
        """Rangli sarlavha"""
        return format_html(
            '<div style="max-width: 220px; line-height: 1.4; font-size: 14px;"><strong style="color: #2c3e50;" title="{}">{}</strong></div>',
            obj.title,
            obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
        )
    colored_title.short_description = 'Maqola'
    
    def author_info(self, obj):
        """Muallif ma'lumotlari"""
        return format_html(
            '<div style="min-width: 140px; line-height: 1.4; font-size: 13px;" title="{} - {} - {}">'
            '<strong style="color: #2c3e50; display: block;">{}</strong>'
            '<small style="display: block; color: #666; font-size: 12px;">{}</small>'
            '</div>',
            obj.author_name,
            obj.author_email,
            obj.author_phone,
            obj.author_name[:22] + '...' if len(obj.author_name) > 22 else obj.author_name,
            obj.author_phone
        )
    author_info.short_description = 'Muallif'
    
    def colored_status(self, obj):
        """Rangli status"""
        status_icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'published': '📰',
        }
        return format_html(
            '<div style="text-align: center; min-width: 50px;">'  
            '<span style="background-color: {}; color: white; padding: 8px 10px; border-radius: 6px; font-size: 18px; display: inline-block; line-height: 1;" title="{}">{}</span>'
            '</div>',
            obj.get_status_display_color(),
            obj.get_status_display(),
            status_icons.get(obj.status, '?')
        )
    colored_status.short_description = 'Holat'
    
    def colored_payment_status(self, obj):
        """Rangli to'lov holati"""
        payment_icons = {
            'pending': '⏳',
            'paid': '✅',
            'refunded': '🔄',
        }
        payment_titles = {
            'pending': "To'lanmagan",
            'paid': "To'langan",
            'refunded': 'Qaytarilgan',
        }
        return format_html(
            '<div style="text-align: center; min-width: 50px;">'  
            '<span style="background-color: {}; color: white; padding: 8px 10px; border-radius: 6px; font-size: 18px; display: inline-block; line-height: 1;" title="{}">{}</span>'
            '</div>',
            obj.get_payment_status_color(),
            payment_titles.get(obj.payment_status, obj.payment_status),
            payment_icons.get(obj.payment_status, '?')
        )
    colored_payment_status.short_description = "To'lov"
    
    def payment_link_status(self, obj):
        """To'lov linki yuborilganlik holati"""
        if obj.payment_link_sent:
            title = f"Yuborilgan: {obj.payment_link_sent_at.strftime('%d.%m.%Y %H:%M')} ({obj.payment_link_sent_count} marta)" if obj.payment_link_sent_at else 'Yuborilgan'
            return format_html(
                '<div style="text-align: center;">'
                '<span style="background-color: #28a745; color: white; padding: 8px 10px; border-radius: 6px; font-size: 18px; display: inline-block; line-height: 1;" title="{}">📧</span>'
                '</div>',
                title
            )
        return format_html(
            '<div style="text-align: center;">'
            '<span style="background-color: #6c757d; color: white; padding: 8px 10px; border-radius: 6px; font-size: 18px; display: inline-block; opacity: 0.5; line-height: 1;" title="Hali yuborilmagan">📧</span>'
            '</div>'
        )
    payment_link_status.short_description = "Link"
    
    def submitted_date(self, obj):
        """Yuborilgan sana"""
        return format_html(
            '<div style="text-align: center; font-size: 13px; line-height: 1.4;" title="{}">'
            '<strong style="color: #2c3e50; display: block;">{}</strong>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.submitted_at.strftime('%d.%m.%Y %H:%M'),
            obj.submitted_at.strftime('%d.%m'),
            obj.submitted_at.strftime('%H:%M')
        )
    submitted_date.short_description = 'Sana'
    
    def action_buttons(self, obj):
        """Harakatlar tugmalari"""
        view_url = reverse('admin:pages_article_view', args=[obj.pk])
        return format_html(
            '<div style="text-align: center;">'
            '<a class="button" style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 6px 10px; text-decoration: none; border-radius: 6px; display: inline-block; font-size: 16px; line-height: 1;" href="{}" title="Ko\'rish">👁️</a>'
            '</div>',
            view_url
        )
    action_buttons.short_description = ''
    
    def pdf_preview(self, obj):
        """PDF ko'rish"""
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" style="padding: 10px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; display: inline-block;">📄 PDF ni ko\'rish</a>',
                obj.pdf_file.url
            )
        return '-'
    pdf_preview.short_description = 'PDF fayl'
    
    def author_contact_info(self, obj):
        """Muallif aloqa ma'lumotlari"""
        return format_html(
            '<div style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff; border-radius: 5px;">'
            '<p><strong>📧 Email:</strong> <a href="mailto:{}">{}</a></p>'
            '<p><strong>📱 Telefon:</strong> {}</p>'
            '<p><strong>🏢 Ish joyi:</strong> {}</p>'
            '<p><strong>🎓 Ilmiy daraja:</strong> {}</p>'
            '<p><strong>🆔 ORCID:</strong> {}</p>'
            '</div>',
            obj.author_email, obj.author_email,
            obj.author_phone,
            obj.author_workplace or '-',
            obj.get_author_degree_label(),
            obj.author_orcid or '-'
        )
    author_contact_info.short_description = 'Aloqa ma\'lumotlari'
    
    def mark_as_paid(self, request, queryset):
        """To'landi deb belgilash"""
        updated = queryset.update(
            payment_status='paid',
            payment_date=timezone.now()
        )
        self.message_user(request, f'{updated} ta maqola to\'landi deb belgilandi.')
    mark_as_paid.short_description = "💰 To'landi deb belgilash"
    
    def send_approval_email(self, article):
        """Tasdiqlash emaili"""
        subject = f"✅ Maqolangiz tasdiqlandi - {article.title}"
        
        context = {
            'article': article,
            'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        }
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #02AB6F 0%, #86DAF1 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">🎉 Tabriklaymiz!</h1>
                </div>
                
                <div style="padding: 30px; background-color: #f9f9f9;">
                    <p style="font-size: 16px;">Hurmatli <strong>{article.author_name}</strong>,</p>
                    
                    <p style="font-size: 16px;">Sizning <strong>"{article.title}"</strong> nomli maqolangiz ko'rib chiqildi va <span style="color: #28a745; font-weight: bold;">TASDIQLANDI</span>! ✅</p>
                    
                    <div style="background-color: white; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <h3 style="color: #28a745; margin-top: 0;">📄 Maqola ma'lumotlari:</h3>
                        <p><strong>Sarlavha:</strong> {article.title}</p>
                        <p><strong>Tasdiqlangan vaqti:</strong> {timezone.now().strftime('%d.%m.%Y %H:%M')}</p>
                        <p><strong>To'lov holati:</strong> {article.get_payment_status_display()}</p>
                    </div>
                    
                    <p style="font-size: 16px;">Keyingi bosqichlar:</p>
                    <ol style="font-size: 15px;">
                        <li>Maqolangiz tahririyat jarayonidan o'tadi</li>
                        <li>Keyingi sonida nashr etiladi</li>
                        <li>Sizga nashr haqida xabar beramiz</li>
                    </ol>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">Savollaringiz bo'lsa, biz bilan bog'laning:</p>
                    <p style="font-size: 14px; color: #666;">📧 {settings.DEFAULT_FROM_EMAIL}</p>
                </div>
                
                <div style="background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 0 0 10px 10px;">
                    <p style="margin: 0; font-size: 12px; color: #999;">© 2026 Ilmiy Jurnal. Barcha huquqlar himoyalangan.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=f"Hurmatli {article.author_name},\n\nSizning maqolangiz tasdiqlandi!\n\nMaqola: {article.title}\n\nIlmiy Jurnal jamoasi",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[article.author_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            print(f"Email yuborishda xatolik: {e}")
    
    def send_rejection_email(self, article, rejection_file=None):
        """Bekor qilish emaili"""
        subject = f"❌ Maqola haqida xabar - {article.title}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">📝 Maqola haqida xabar</h1>
                </div>
                
                <div style="padding: 30px; background-color: #f9f9f9;">
                    <p style="font-size: 16px;">Hurmatli <strong>{article.author_name}</strong>,</p>
                    
                    <p style="font-size: 16px;">Sizning <strong>"{article.title}"</strong> nomli maqolangiz ko'rib chiqildi.</p>
                    
                    <div style="background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <h3 style="color: #856404; margin-top: 0;">⚠️ Bekor qilish sababi:</h3>
                        <p style="font-size: 15px; white-space: pre-wrap;">{article.rejection_reason}</p>
                    </div>
                    
                    <div style="background-color: white; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0;">
                        <h3 style="color: #007bff; margin-top: 0;">💡 Keyingi qadamlar:</h3>
                        <ul style="font-size: 15px;">
                            <li>Yuqorida ko'rsatilgan kamchiliklarni tuzating</li>
                            <li>Maqolani qayta tayyorlab, yana yuboring</li>
                            <li>Savollaringiz bo'lsa, biz bilan bog'laning</li>
                        </ul>
                    </div>
                    
                    <p style="font-size: 16px; margin-top: 30px;">Biz sizning ilmiy faoliyatingizni qadrlаymiz va keyingi maqolalaringizni kutib qolamiz!</p>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">Savollaringiz bo'lsa:</p>
                    <p style="font-size: 14px; color: #666;">📧 {settings.DEFAULT_FROM_EMAIL}</p>
                </div>
                
                <div style="background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 0 0 10px 10px;">
                    <p style="margin: 0; font-size: 12px; color: #999;">© 2026 Ilmiy Jurnal. Barcha huquqlar himoyalangan.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=f"Hurmatli {article.author_name},\n\nSizning maqolangiz haqida xabar:\n\nMaqola: {article.title}\n\nBekor qilish sababi:\n{article.rejection_reason}\n\nIlmiy Jurnal jamoasi",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[article.author_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # PDF faylni biriktirish
            if article.pdf_file:
                email.attach_file(article.pdf_file.path)
            
            # Qo'shimcha fayllarni biriktirish
            if article.additional_files:
                email.attach_file(article.additional_files.path)
            
            # Bekor qilish faylini biriktirish (agar yuklangan bo'lsa)
            if rejection_file:
                email.attach(rejection_file.name, rejection_file.read(), rejection_file.content_type)
            
            email.send()
        except Exception as e:
            print(f"Email yuborishda xatolik: {e}")
    
    def send_payment_email(self, article):
        """To'lov uchun email yuborish"""
        subject = f"💰 To'lov haqida ma'lumot - {article.title}"
        
        # Telegram bot ma'lumotlari (siz o'zingizning ma'lumotlaringizni kiriting)
        telegram_bot_username = "@YourBotUsername"  # O'zgartiring
        telegram_phone = "+998901234567"  # O'zgartiring
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #0088cc 0%, #00c6ff 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">💰 To'lov Ma'lumotlari</h1>
                </div>
                
                <div style="padding: 30px; background-color: #f9f9f9;">
                    <p style="font-size: 16px;">Hurmatli <strong>{article.author_name}</strong>,</p>
                    
                    <p style="font-size: 16px;">Sizning <strong>"{article.title}"</strong> nomli maqolangiz muvaffaqiyatli qabul qilindi! 🎉</p>
                    
                    <div style="background-color: #d1ecf1; padding: 20px; border-left: 4px solid #0c5460; margin: 20px 0; border-radius: 5px;">
                        <h3 style="color: #0c5460; margin-top: 0;">📋 Keyingi qadam:</h3>
                        <p style="font-size: 15px;">Maqolangizni nashr etish jarayonini davom ettirish uchun to'lovni tasdiqlashingiz kerak.</p>
                    </div>
                    
                    <div style="background-color: white; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 5px;">
                        <h3 style="color: #28a745; margin-top: 0;">💳 To'lov qilish uchun:</h3>
                        <p style="font-size: 15px;"><strong>1-qadam:</strong> Telegram orqali to'lov qiling</p>
                        <p style="font-size: 15px;"><strong>2-qadam:</strong> Quyidagi ma'lumotlarni yuborish orqali to'lovni tasdiqlang:</p>
                        
                        <div style="background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border: 1px solid #dee2e6;">
                            <p style="margin: 5px 0;"><strong>📱 Telefon raqamingiz:</strong> {article.author_phone}</p>
                            <p style="margin: 5px 0;"><strong>📧 Email:</strong> {article.author_email}</p>
                            <p style="margin: 5px 0;"><strong>📄 Maqola nomi:</strong> {article.title}</p>
                        </div>
                    </div>
                    
                    <div style="background-color: #e7f3ff; padding: 20px; border-left: 4px solid #0088cc; margin: 20px 0; border-radius: 5px;">
                        <h3 style="color: #0088cc; margin-top: 0;">📞 Bog'lanish uchun:</h3>
                        <p style="font-size: 15px; margin: 5px 0;"><strong>Telegram:</strong> <a href="https://t.me/{telegram_bot_username[1:]}" style="color: #0088cc; text-decoration: none;">{telegram_bot_username}</a></p>
                        <p style="font-size: 15px; margin: 5px 0;"><strong>Telefon:</strong> {telegram_phone}</p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #856404; margin: 20px 0; border-radius: 5px;">
                        <p style="font-size: 14px; color: #856404; margin: 0;"><strong>⚠️ Muhim:</strong> To'lovni amalga oshirgandan so'ng, yuqoridagi ma'lumotlarni Telegram botga yuboring. To'lov tasdiqlanganidan keyin maqolangiz nashr jarayoniga qabul qilinadi.</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">Savollaringiz bo'lsa, biz bilan bog'laning:</p>
                    <p style="font-size: 14px; color: #666;">📧 {settings.DEFAULT_FROM_EMAIL}</p>
                </div>
                
                <div style="background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 0 0 10px 10px;">
                    <p style="margin: 0; font-size: 12px; color: #999;">© 2026 Ilmiy Jurnal. Barcha huquqlar himoyalangan.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=f"""Hurmatli {article.author_name},

Sizning maqolangiz muvaffaqiyatli qabul qilindi!

Maqola: {article.title}

To'lovni tasdiqlash uchun quyidagi ma'lumotlarni Telegram botga yuboring:
- Telefon: {article.author_phone}
- Email: {article.author_email}
- Maqola: {article.title}

Telegram: {telegram_bot_username}
Telefon: {telegram_phone}

Ilmiy Jurnal jamoasi""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[article.author_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            print(f"Email yuborishda xatolik: {e}")
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(EditorialMember)
class EditorialMemberAdmin(admin.ModelAdmin):
    """Tahririyat a'zolari admin paneli"""
    
    list_display = ['full_name', 'position', 'academic_degree', 'workplace', 'is_active']
    list_filter = ['position', 'is_active']
    search_fields = ['full_name', 'workplace', 'academic_degree']
    list_editable = ['is_active']
    ordering = ['full_name']
    
    fields = ('full_name', 'position', 'academic_degree', 'workplace', 'photo', 'is_active')


@admin.register(RegulatoryDocument)
class RegulatoryDocumentAdmin(admin.ModelAdmin):
    """Meyoriy hujjatlar admin paneli"""
    
    list_display = ['image_preview', 'is_active', 'uploaded_at']
    list_filter = ['is_active', 'uploaded_at']
    list_editable = ['is_active']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    fields = ('image', 'is_active')
    
    def image_preview(self, obj):
        """Rasm ko'rinishi"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: auto; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Ko\'rinish'
    
    def has_module_permission(self, request):
        """Modul ruxsati"""
        return request.user.is_staff
    
    class Media:
        css = {
            'all': ('admin/css/regulatory_custom.css',)
        }


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Yangiliklar admin paneli"""
    
    list_display = ['image_preview', 'title', 'category', 'author', 'views', 'published_date', 'is_active']
    list_filter = ['category', 'is_active', 'published_date']
    search_fields = ['title', 'content', 'author']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    ordering = ['-published_date']
    readonly_fields = ['views', 'published_date']
    
    fields = ('title', 'slug', 'category', 'image', 'excerpt', 'content', 'author', 'is_active')
    
    def image_preview(self, obj):
        """Rasm preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Rasm'
    
    def save_model(self, request, obj, form, change):
        """Saqlashda slug avtomatik yaratish"""
        if not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(obj.title)
        super().save_model(request, obj, form, change)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """E'lonlar admin paneli"""
    
    list_display = ['icon_display', 'title', 'category_display', 'priority_display', 'validity_status_display', 'published_date', 'is_active']
    list_filter = ['category', 'is_active', 'published_date', 'validity_end']
    search_fields = ['title', 'content']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    ordering = ['-published_date']
    readonly_fields = ['published_date']
    
    fields = ('title', 'slug', 'category', 'excerpt', 'content', 'validity_start', 'validity_end', 'is_active')
    
    def icon_display(self, obj):
        """Icon ko'rinishi - kategoriyaga qarab"""
        icons = {
            'warning': '⚠️',
            'info': 'ℹ️',
            'document': '📄'
        }
        return format_html(
            '<span style="font-size: 24px;">{}</span>',
            icons.get(obj.get_icon(), '📄')
        )
    icon_display.short_description = 'Icon'
    
    def category_display(self, obj):
        """Kategoriya ko'rinishi"""
        return obj.get_category_display()
    category_display.short_description = 'Kategoriya'
    
    def priority_display(self, obj):
        """Priority rangli ko'rinish - kategoriyaga qarab"""
        colors = {
            'yuqori': '#dc3545',
            'orta': '#ffc107',
            'past': '#28a745'
        }
        priority = obj.get_priority()
        priority_labels = {
            'yuqori': 'Yuqori',
            'orta': 'O\'rta',
            'past': 'Past'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            colors.get(priority, '#6c757d'),
            priority_labels.get(priority, 'O\'rta')
        )
    priority_display.short_description = 'Muhimlik'
    
    def validity_status_display(self, obj):
        """Amal qilish holati ko'rinishi"""
        if not obj.validity_end:
            return format_html(
                '<span style="color: #6c757d; font-size: 12px;">Muddat yo\'q</span>'
            )
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if today > obj.validity_end:
            return format_html(
                '<span style="color: #dc3545; font-weight: 600;">❌ Muddati o\'tgan</span>'
            )
        elif today == obj.validity_end:
            return format_html(
                '<span style="color: #ffc107; font-weight: 600;">⏰ Bugun tugaydi</span>'
            )
        else:
            days_left = (obj.validity_end - today).days
            if days_left <= 3:
                color = '#ffc107'
            else:
                color = '#28a745'
            return format_html(
                '<span style="color: {}; font-weight: 600;">✅ {} kun qoldi</span>',
                color, days_left
            )
    validity_status_display.short_description = 'Amal qilish holati'
    
    def save_model(self, request, obj, form, change):
        """Saqlashda slug avtomatik yaratish"""
        if not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(obj.title)
        super().save_model(request, obj, form, change)

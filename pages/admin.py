from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import (
    Announcement, Article, Author, EditorialMember, News,
    RegulatoryDocument, Subscriber, Volume, VolumeArticle,
)


# Article va Author modellari admin paneldan olib tashlandi


@admin.register(EditorialMember)
class EditorialMemberAdmin(admin.ModelAdmin):
    """Tahririyat a'zolari admin paneli"""
    
    list_display = ['full_name', 'position', 'academic_degree', 'workplace', 'is_active']
    list_filter = ['position', 'is_active']
    search_fields = ['full_name', 'workplace', 'academic_degree']
    list_editable = ['is_active']
    ordering = ['full_name']


@admin.register(RegulatoryDocument)
class RegulatoryDocumentAdmin(admin.ModelAdmin):
    """Meyoriy hujjatlar admin paneli"""
    
    list_display = ['image_preview', 'is_active', 'uploaded_at']
    list_filter = ['is_active', 'uploaded_at']
    list_editable = ['is_active']
    ordering = ['-uploaded_at']
    
    def image_preview(self, obj):
        """Rasm ko'rinishi"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 5px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Rasm'


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Yangiliklar admin paneli"""
    
    list_display = ['title', 'published_date', 'views', 'is_active']
    list_filter = ['is_active', 'published_date']
    search_fields = ['title', 'content']
    list_editable = ['is_active']
    ordering = ['-published_date']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """E'lonlar admin paneli"""
    
    list_display = ['title_with_icon', 'category', 'validity_start', 'validity_end', 'is_active', 'priority_display']
    list_filter = ['category', 'is_active', 'published_date']
    search_fields = ['title', 'content']
    list_editable = ['is_active']
    ordering = ['-published_date']
    actions = ['send_email_to_all_subscribers']

    def _send_emails(self, request, ann):
        """Barcha faol obunachilarga e'lon emaili yuborish"""
        subs = Subscriber.objects.filter(is_active=True)
        if not subs.exists():
            return 0
        site_url = request.build_absolute_uri('/')
        elon_url = f"{site_url.rstrip('/')}/elonlar/{ann.slug}/"
        sent = 0
        for sub in subs:
            try:
                html = f"""
                <html><body style="font-family:Arial,sans-serif;line-height:1.7;color:#333;margin:0;padding:0">
                <div style="max-width:620px;margin:30px auto;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.08)">
                  <div style="background:linear-gradient(135deg,#02AB6F,#0288D1);padding:40px 30px;text-align:center">
                    <div style="font-size:44px;margin-bottom:10px">&#128226;</div>
                    <h1 style="color:white;margin:0;font-size:24px;font-weight:700">Yangi E'lon!</h1>
                    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px">Lifelong Learning Ilmiy Jurnali</p>
                  </div>
                  <div style="padding:35px 30px;background:#ffffff">
                    <p style="margin-top:0;font-size:15px">Hurmatli <strong>{sub.full_name}</strong>,</p>
                    <p style="font-size:15px;color:#444">Lifelong Learning Ilmiy Jurnalidan yangi e'lon mavjud:</p>
                    <div style="background:#f8fff9;padding:22px;border:1px solid #c3e6cb;border-radius:8px;margin:20px 0">
                      <h2 style="color:#155724;margin:0 0 12px;font-size:18px">{ann.title}</h2>
                      <p style="color:#444;margin:0;font-size:14px;line-height:1.7">{ann.excerpt}</p>
                    </div>
                    <div style="text-align:center;margin:25px 0">
                      <a href="{elon_url}" style="background:linear-gradient(135deg,#02AB6F,#0288D1);color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;display:inline-block">&#128204; To'liq o'qish</a>
                    </div>
                    <div style="background:#f0f8ff;padding:18px;border:1px solid #b8daff;border-radius:8px;margin-top:20px">
                      <p style="margin:0 0 6px;font-size:13px;color:#004085"><strong>&#128222; Bog'lanish:</strong></p>
                      <p style="margin:4px 0;font-size:13px">&#128231; <a href="mailto:{settings.CONTACT_EMAIL}" style="color:#0056b3">{settings.CONTACT_EMAIL}</a></p>
                      <p style="margin:4px 0;font-size:13px">&#128241; +998 97 736 20 11</p>
                      <p style="margin:4px 0;font-size:13px">&#9992;&#65039; <a href="https://t.me/XURSHID_HAMD11" style="color:#0056b3">@XURSHID_HAMD11</a></p>
                    </div>
                  </div>
                  <div style="background:#f8f9fa;padding:16px 30px;text-align:center;border-top:1px solid #e9ecef">
                    <p style="margin:0;color:#6c757d;font-size:12px">&#169; Lifelong Learning Ilmiy Jurnali &nbsp;|&nbsp; Buxoro sh., Akademik Ibrohim Mo'minov ko'chasi 28/2</p>
                    <p style="margin:6px 0 0;font-size:11px;color:#aaa">Obunani bekor qilish: <a href="mailto:{settings.CONTACT_EMAIL}?subject=Obunani+bekor+qilish" style="color:#aaa">{settings.CONTACT_EMAIL}</a></p>
                  </div>
                </div>
                </body></html>"""
                em = EmailMultiAlternatives(
                    subject=f"Yangi e'lon: {ann.title}",
                    body=ann.excerpt,
                    from_email=settings.CONTACT_EMAIL,
                    to=[sub.email],
                )
                em.attach_alternative(html, "text/html")
                em.send()
                sent += 1
            except Exception as e:
                print(f"Email xato ({sub.email}): {e}")
        return sent

    def save_model(self, request, obj, form, change):
        """Yangi e'lon saqlanganda obunachilarga email yuborish (faqat yangi qo'shilganda)"""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new and obj.is_active:
            sent = self._send_emails(request, obj)
            if sent > 0:
                self.message_user(request, f"E'lon saqlandi. {sent} ta obunachiga email yuborildi.")
            else:
                self.message_user(request, "E'lon saqlandi. (Faol obunachi yo'q yoki email yuborishda xato.)")

    @admin.action(description="Tanlangan e'lonlarni barcha obunachilarga yuborish")
    def send_email_to_all_subscribers(self, request, queryset):
        total = 0
        for ann in queryset:
            total += self._send_emails(request, ann)
        self.message_user(request, f"{queryset.count()} ta e'lon, jami {total} ta email yuborildi.")
    
    def title_with_icon(self, obj):
        """Sarlavha ikonka bilan"""
        icon_display = {
            'warning': '⚠️',
            'info': 'ℹ️',
            'document': '📄',
        }
        return format_html(
            '<span style="font-size: 18px;">{}</span> <strong>{}</strong>',
            icon_display.get(obj.get_icon(), 'ℹ️'),
            obj.title
        )
    title_with_icon.short_description = 'E\'lon'
    
    def priority_display(self, obj):
        """Prioritet ko'rinishi"""
        colors = {
            'yuqori': '#dc3545',
            'orta': '#ffc107',
            'past': '#28a745',
        }
        labels = {
            'yuqori': 'Yuqori',
            'orta': 'O\'rta',
            'past': 'Past',
        }
        priority = obj.get_priority()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            colors.get(priority, '#6c757d'),
            labels.get(priority, 'Noma\'lum')
        )
    priority_display.short_description = 'Muhimlik'


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """Obunachlar admin paneli"""
    list_display = ['full_name', 'email', 'source_display', 'is_active', 'created_at']
    list_filter = ['source', 'is_active', 'created_at']
    search_fields = ['full_name', 'email']
    list_editable = ['is_active']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    list_per_page = 50

    class Media:
        css = {'all': ('admin/css/subscriber_compact.css',)}

    def source_display(self, obj):
        labels = {'newsletter': '📨 Obuna formasi', 'article': '📄 Maqola yuborish'}
        return labels.get(obj.source, obj.source)
    source_display.short_description = 'Manba'


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'volume_number', 'issue_number', 'status', 'articles_count']
    list_filter = ['status', 'year', 'subject']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(VolumeArticle)
class VolumeArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'volume', 'authors', 'published_date', 'views_count']
    list_filter = ['volume', 'category']
    search_fields = ['title', 'authors', 'keywords']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'status', 'payment_status', 'submitted_at']
    list_filter = ['status', 'payment_status', 'category']
    search_fields = ['title', 'author_name', 'author_email']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'total_articles', 'last_submission']
    search_fields = ['full_name', 'email', 'phone']

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('til/<str:lang_code>/', views.set_language, name='set_language'),
    path('haqida/', views.haqida, name='haqida'),
    path('aloqa/', views.aloqa, name='aloqa'),
    path('maqola-berish/', views.maqola_berish, name='maqola_berish'),
    path('tahrir-hayati/', views.tahrir_hayati, name='tahrir_hayati'),
    path('jurnal-talablari/', views.jurnal_talablari, name='jurnal_talablari'),
    path('meyoriy-hujjatlar/', views.meyoriy_hujjatlar, name='meyoriy_hujjatlar'),
    path('arxiv/', views.arxiv, name='arxiv'),
    path('maqolalar/', views.maqolalar, name='maqolalar'),
    path('arxiv/<slug:slug>/', views.arxiv_detail, name='arxiv_detail'),
    path('arxiv/<slug:slug>/sertifikatlar/', views.volume_certificates_download, name='volume_certificates_download'),
    path('arxiv/<slug:volume_slug>/maqola/<slug:article_slug>/', views.arxiv_article_detail, name='arxiv_article_detail'),
    path('arxiv/<slug:volume_slug>/maqola/<slug:article_slug>/yuklab-olish/', views.arxiv_article_download, name='arxiv_article_download'),
    path('arxiv/<slug:volume_slug>/maqola/<slug:article_slug>/oqish/', views.arxiv_article_pdf_redirect, name='arxiv_article_pdf_redirect'),
    path('yangiliklar/', views.yangiliklar, name='yangiliklar'),
    path('yangiliklar/<slug:slug>/', views.yangilik_detail, name='yangilik_detail'),
    path('elonlar/', views.elonlar, name='elonlar'),
    path('elonlar/<slug:slug>/', views.elon_detail, name='elon_detail'),
    path('qidiruv/', views.qidiruv, name='qidiruv'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('feed/rss/', views.articles_rss, name='articles_rss'),
    
    # Admin sahifalar
    path('admin-panel/foydalanuvchilar/', views.admin_foydalanuvchilar, name='admin_foydalanuvchilar'),
    path('admin-panel/foydalanuvchi/<int:author_id>/', views.admin_foydalanuvchi_detail, name='admin_foydalanuvchi_detail'),
    path('admin-panel/article/<int:article_id>/approve/', views.admin_article_approve, name='admin_article_approve'),
    path('admin-panel/article/<int:article_id>/confirm-payment/', views.admin_article_confirm_payment, name='admin_article_confirm_payment'),
    path('admin-panel/article/<int:article_id>/reject/', views.admin_article_reject, name='admin_article_reject'),
    path('admin-panel/article/<int:article_id>/send-payment/', views.admin_article_send_payment, name='admin_article_send_payment'),
    path('admin-panel/article/<int:article_id>/assign-reviewer/', views.admin_article_assign_reviewer, name='admin_article_assign_reviewer'),
    path('admin-panel/taqrizchilar/', views.admin_taqrizchilar, name='admin_taqrizchilar'),
    path('admin-panel/tomlar/', views.admin_tomlar, name='admin_tomlar'),
    path('admin-panel/tomlar/<int:volume_id>/', views.admin_tom_detail, name='admin_tom_detail'),
    path('admin-panel/obunachlar/', views.admin_obunachlar, name='admin_obunachlar'),
    path('obuna/', views.subscribe, name='subscribe'),
    path('tomlar/<slug:slug>/', views.volume_detail_redirect, name='volume_detail_public'),
    path('tomlar/<slug:slug>/yuklab-olish/', views.volume_pdf_download, name='volume_pdf_download'),
    path('tomlar/<slug:slug>/maqola/<int:article_id>/sertifikat/', views.article_certificate_download, name='article_certificate_download'),

    # Taqrizchilar
    path('taqrizchi/login/', views.reviewer_login, name='reviewer_login'),
    path('taqrizchi/chiqish/', views.reviewer_logout, name='reviewer_logout'),
    path('taqrizchi/', views.reviewer_profil, name='reviewer_profil'),
    path('taqrizchi/maqola/<int:review_id>/', views.reviewer_article_detail, name='reviewer_article_detail'),
    path('taqrizchi/maqola/<int:review_id>/tasdiqlash/', views.reviewer_article_approve, name='reviewer_article_approve'),
    path('taqrizchi/maqola/<int:review_id>/rad-etish/', views.reviewer_article_reject, name='reviewer_article_reject'),
]

from django.conf import settings

if settings.DEBUG:
    urlpatterns += [
        path('404-preview/', views.page_not_found_preview, name='error404_preview'),
    ]

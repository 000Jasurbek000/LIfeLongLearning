from .i18n import get_language, get_language_info, get_languages
from .presenters import get_site_stats


def site_i18n(request):
    language_code = get_language(request)
    return {
        'current_language': get_language_info(language_code),
        'available_languages': get_languages(),
    }


def site_stats(request):
    stats = get_site_stats()
    return {
        'site_stats': stats,
        'hero_stats': {
            'articles': stats['published_articles'],
            'authors': stats['authors_count'],
            'issues': stats['issues_count'],
        },
    }

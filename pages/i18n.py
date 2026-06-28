import json
from pathlib import Path

from django.conf import settings


DEFAULT_LANGUAGE = 'uz'
LANGUAGE_SESSION_KEY = 'site_language'
SUPPORTED_LANGUAGES = {
    'uz': {
        'code': 'uz',
        'label': "O'zbekcha",
        'short': "O'Z",
        'html_lang': 'uz',
        'flag': '🇺🇿',
    },
    'ru': {
        'code': 'ru',
        'label': 'Русский',
        'short': 'РУ',
        'html_lang': 'ru',
        'flag': '🇷🇺',
    },
    'en': {
        'code': 'en',
        'label': 'English',
        'short': 'EN',
        'html_lang': 'en',
        'flag': '🇬🇧',
    },
}

LOCALES_DIR = Path(settings.BASE_DIR) / 'pages' / 'locales'
_translation_cache: dict[str, tuple[float, dict]] = {}


def load_translations(language_code: str) -> dict:
    language_code = normalize_language(language_code)
    file_path = LOCALES_DIR / f'{language_code}.json'
    if not file_path.exists():
        return {}
    mtime = file_path.stat().st_mtime
    cached = _translation_cache.get(language_code)
    if cached and cached[0] == mtime:
        return cached[1]
    with file_path.open('r', encoding='utf-8') as file:
        data = json.load(file)
    _translation_cache[language_code] = (mtime, data)
    return data


def normalize_language(language_code: str | None) -> str:
    if language_code in SUPPORTED_LANGUAGES:
        return language_code
    return DEFAULT_LANGUAGE


def get_language(request=None) -> str:
    if request is None:
        return DEFAULT_LANGUAGE

    session_language = request.session.get(LANGUAGE_SESSION_KEY)
    if session_language in SUPPORTED_LANGUAGES:
        return session_language

    query_language = request.GET.get('lang')
    if query_language in SUPPORTED_LANGUAGES:
        return query_language

    return DEFAULT_LANGUAGE


def get_language_info(language_code: str | None = None) -> dict:
    return SUPPORTED_LANGUAGES[normalize_language(language_code)]


def get_languages() -> list[dict]:
    return [SUPPORTED_LANGUAGES[code] for code in SUPPORTED_LANGUAGES]


def resolve_key(data: dict, key: str):
    value = data
    for part in key.split('.'):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def translate(key: str, language_code: str | None = None, fallback: str | None = None):
    language_code = normalize_language(language_code)
    translations = load_translations(language_code)
    value = resolve_key(translations, key)
    if value is not None:
        return value

    if language_code != DEFAULT_LANGUAGE:
        default_translations = load_translations(DEFAULT_LANGUAGE)
        default_value = resolve_key(default_translations, key)
        if default_value is not None:
            return default_value

    return fallback if fallback is not None else key

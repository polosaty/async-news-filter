from . import inosmi_ru
from .exceptions import ArticleNotFound

__all__ = ['SANITIZERS', 'TITLE_PARSERS', 'ArticleNotFound']

SANITIZERS = {
    'inosmi_ru': inosmi_ru.sanitize,
}

TITLE_PARSERS = {
    'inosmi_ru': inosmi_ru.get_title,
}

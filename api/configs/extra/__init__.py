from configs.extra.notion_config import NotionConfig
from configs.extra.sentry_config import SentryConfig
from configs.extra.vvvapp_config import VvvappConfig


class ExtraServiceConfig(
    # place the configs in alphabet order
    NotionConfig,
    SentryConfig,
    VvvappConfig,
):
    pass

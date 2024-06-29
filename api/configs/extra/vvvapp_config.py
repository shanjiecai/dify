
from pydantic import BaseModel, Field


class VvvappConfig(BaseModel):
    """
    Vvvapp configs
    """
    OPENAI_API_KEY: str = Field(
        description='openai api key',
        default='',
    )

    NEWS_API_KEY: str = Field(
        description='news api key',
        default='',
    )

    FEISHU_ALERT_URL: str = Field(
        description='feishu alert url',
        default='',
    )

    APP_ENDPOINT: str = Field(
        description='app endpoint',
        default='',
    )

    ES_HOST: str = Field(
        description='es host',
        default='localhost',
    )

    ROLE_MODEL_CUSTOMIZE_SERVICE_URL: str = Field(
        description='role model customize service url',
        default='',
    )
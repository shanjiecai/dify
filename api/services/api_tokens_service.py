

from extensions.ext_database import db
from models.model import ApiToken, App


class APITokensService:
    @classmethod
    def get_api_tokens_from_app_name(cls, app_name: str) -> ApiToken:
        app = db.session.query(App).filter_by(name=app_name).first()
        # print(app.id)
        api_token = db.session.query(ApiToken).filter_by(
            app_id=app.id
        ).first()
        return api_token


if __name__ == "__main__":
    pass

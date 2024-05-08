import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union

from flask import Flask
from sqlalchemy import or_

# from controllers.app_api.openai_base_request import compare_similarity, generate_response
from controllers.app_api.plan.generate_plan_from_conversation import (
    generate_plan_from_conversation,
    generate_plan_introduction,
)
from controllers.app_api.plan.judge_plan import judge_plan
from core.app.entities.app_invoke_entities import InvokeFrom
from core.llm_generator.llm_generator import LLMGenerator
from core.prompt_const import plan_summary_system_prompt

# from core.generator.llm_generator import LLMGenerator
from extensions.ext_database import db
from libs.infinite_scroll_pagination import InfiniteScrollPagination
from models.account import Account
from models.model import App, Conversation, ConversationPlanDetail, EndUser, Message
from mylogger import logger
from services.errors.conversation import ConversationNotExistsError, LastConversationNotExistsError
from services.errors.message import MessageNotExistsError
from services.openai_base_request_service import compare_similarity, generate_response


class ConversationService:
    @classmethod
    def pagination_by_last_id(cls, app_model: App, user: Optional[Union[Account, EndUser]],
                              last_id: Optional[str], limit: int,
                              invoke_from: InvokeFrom,
                              include_ids: Optional[list] = None,
                              exclude_ids: Optional[list] = None) -> InfiniteScrollPagination:
        if not user:
            return InfiniteScrollPagination(data=[], limit=limit, has_more=False)

        base_query = db.session.query(Conversation).filter(
            Conversation.is_deleted == False,
            # Conversation.app_id == app_model.id,
            Conversation.from_source == ('api' if isinstance(user, EndUser) else 'console'),
            Conversation.from_end_user_id == (user.id if isinstance(user, EndUser) else None),
            Conversation.from_account_id == (user.id if isinstance(user, Account) else None),
            or_(Conversation.invoke_from.is_(None), Conversation.invoke_from == invoke_from.value)
        )

        if include_ids is not None:
            base_query = base_query.filter(Conversation.id.in_(include_ids))

        if exclude_ids is not None:
            base_query = base_query.filter(~Conversation.id.in_(exclude_ids))

        if last_id:
            last_conversation = base_query.filter(
                Conversation.id == last_id,
            ).first()

            if not last_conversation:
                raise LastConversationNotExistsError()

            conversations = base_query.filter(
                Conversation.created_at < last_conversation.created_at,
                Conversation.id != last_conversation.id
            ).order_by(Conversation.created_at.desc()).limit(limit).all()
        else:
            conversations = base_query.order_by(Conversation.created_at.desc()).limit(limit).all()

        has_more = False
        if len(conversations) == limit:
            current_page_first_conversation = conversations[-1]
            rest_count = base_query.filter(
                Conversation.created_at < current_page_first_conversation.created_at,
                Conversation.id != current_page_first_conversation.id
            ).count()

            if rest_count > 0:
                has_more = True

        return InfiniteScrollPagination(
            data=conversations,
            limit=limit,
            has_more=has_more
        )

    @classmethod
    def rename(cls, app_model: App, conversation_id: str,
               user: Optional[Union[Account, EndUser]], name: str, auto_generate: bool):
        conversation = cls.get_conversation(app_model, conversation_id, user)

        if auto_generate:
            return cls.auto_generate_name(app_model, conversation)
        else:
            conversation.name = name
            db.session.commit()

        return conversation

    @classmethod
    def auto_generate_name(cls, app_model: App, conversation: Conversation):
        # get conversation first message
        message = db.session.query(Message) \
            .filter(
                Message.app_id == app_model.id,
                Message.conversation_id == conversation.id
            ).order_by(Message.created_at.asc()).first()

        if not message:
            raise MessageNotExistsError()

        # generate conversation name
        try:
            name = LLMGenerator.generate_conversation_name(app_model.tenant_id, message.query)
            conversation.name = name
        except:
            pass

        db.session.commit()

        return conversation

    @classmethod
    def get_conversation(cls, app_model: Optional[App] = None,
                         conversation_id: str = None,
                         # , user: Optional[Union[Account, EndUser]]
                         ):
        conversation = db.session.query(Conversation) \
            .filter(
            Conversation.id == conversation_id,
            # Conversation.app_id == app_model.id,
            # Conversation.from_source == ('api' if isinstance(user, EndUser) else 'console'),
            # Conversation.from_end_user_id == (user.id if isinstance(user, EndUser) else None),
            # Conversation.from_account_id == (user.id if isinstance(user, Account) else None),
            Conversation.is_deleted == False
        ).first()

        if not conversation:
            raise ConversationNotExistsError()

        return conversation

    @classmethod
    def delete(cls, app_model: App, conversation_id: str, user: Optional[Union[Account, EndUser]]):
        conversation = cls.get_conversation(app_model, conversation_id, user)

        conversation.is_deleted = True
        db.session.commit()

    @classmethod
    def generate_plan(cls, conversation_id: str, plan: str = None, outer_history_str: str = None):
        history_str = ""
        plan_detail_dict = {}
        if not outer_history_str:
            conversation = cls.get_conversation(conversation_id=conversation_id)
            # if not conversation.plan_question_invoke_plan and not plan:
            #     return None
            plan = plan if plan else conversation.plan_question_invoke_plan

            messages = db.session.query(Message).filter(
                Message.conversation_id == conversation.id,
            ).order_by(Message.created_at.desc()).limit(10).all()
            messages = list(reversed(messages))
            for message in messages:
                if messages.index(message) + 1 < len(messages):
                    next_message = messages[messages.index(message) + 1]
                    if (message.answer is None or message.answer == "") and message.query == next_message.query and \
                            message.role == next_message.role and next_message.answer is not None and \
                            next_message.answer != "":
                        continue
                if not message.role:
                    history_str += "User: " + message.query + "\n"
                else:
                    history_str += message.role + ": " + message.query + "\n"
                if message.answer:
                    if not message.assistant_name:
                        history_str += "Assistant: " + message.answer + "\n"
                    else:
                        history_str += message.assistant_name + ": " + message.answer + "\n"
            if not plan:
                plan = judge_plan(history_str)
            plan_detail = generate_plan_from_conversation(history_str, plan)
        else:
            if not plan:
                plan = judge_plan(history_str)
            plan_detail = generate_plan_from_conversation(outer_history_str, plan)

        goals = []
        day = 1
        for k, v in plan_detail.items():
            if not isinstance(v, list):
                continue
            goals.append({
                "day": day,
                "title": k,
                "detail": v
            })
            day += 1
        days = len(goals)
        plan_detail_dict["goals"] = goals
        plan_detail_dict["days"] = days
        plan_detail_dict["tags"] = compare_similarity(plan)

        with ThreadPoolExecutor(max_workers=2) as executor:
            summary_system_prompt = plan_summary_system_prompt
            summary_response = executor.submit(generate_response, history_str, summary_system_prompt)
            introduction_response = executor.submit(generate_plan_introduction, json.dumps(plan_detail))
            chat_summary = summary_response.result().choices[0].message.content
            introduction = introduction_response.result()
            plan_detail_dict["chat_summary"] = chat_summary
            plan_detail_dict["description"] = introduction
        # print(plan_detail_dict)
        # introduction = generate_plan_introduction(json.dumps(plan_detail))
        # plan_detail_dict["description"] = introduction
        return plan_detail_dict, plan, history_str if not outer_history_str else outer_history_str

    @classmethod
    def generate_plan_and_notice_app(cls, flask_app: Flask,  conversation_id: str, plan: str = None):
        try:
            with flask_app.app_context():
                plan_detail, plan, history_str = cls.generate_plan(conversation_id, plan)
                conversation_plan_detail = ConversationPlanDetail(
                    conversation_id=conversation_id,
                    plan=plan,
                    plan_detail_list=[plan_detail],
                    plan_conversation_history=history_str
                )
                db.session.add(conversation_plan_detail)
                db.session.commit()
                # notice app
                # TODO

                return
        except:
            logger.info(f"generate_plan_and_notice_app error: {traceback.format_exc(limit=10)}")


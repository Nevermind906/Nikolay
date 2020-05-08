# coding=utf-8
from datetime import datetime, time, date, timedelta, timezone
from vk_api.utils import get_random_id
import json


def send_msg(vk_api, event, response="", attachment=""):
    if event.from_user:
        vk_api.messages.send(
            user_id=event.raw["object"]["from_id"],
            random_id=get_random_id(),
            message=response,
            attachment=attachment
        )
    elif event.from_chat: #Если написали в Беседе
        vk_api.messages.send(
            chat_id=int(event.chat_id),
            random_id=get_random_id(),
            message=response,
            attachment=attachment
        )

def load_config():
    with open('config/config.json') as f:
        return json.load(f)

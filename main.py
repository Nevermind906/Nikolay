# coding=utf-8
import sys
sys.path.insert(1, './bot/')
sys.path.insert(1, './data/')
from bot import Bot
import utility
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from requests.exceptions import RequestException
import re
import traceback
from datetime import datetime, time, date
from time import sleep
from vk_api.exceptions import ApiError


def run():
    try:
        config = utility.load_config()
        vk_session = VkApi(token=config["token"])
        vk_api = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, config["group_id"])
        bot = Bot()
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
           #Слушаем longpoll, если пришло сообщение то:
                text = re.match(r"(\W\w*)(.*)", event.raw["object"]["text"], flags = re.DOTALL)
                command = text.group(1).strip()
                message = text.group(2).strip()
                response = bot.responde(command, message)
                utility.send_msg(vk_api, event, response)

    except (RequestException, ApiError) as e:
        try:
            with open("./log/request_errors.log", mode="a") as log:
                log.write(str(datetime.now(timezone(timedelta(hours=3)))) + '\n')
                log.write(traceback.format_exc())
                log.write(str(e) + '\n')
                print(e)
        except OSError:
            print("Error occured while opening log file")
        run()

if __name__ == "__main__":
    run()

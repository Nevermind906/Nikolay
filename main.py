# coding=utf-8
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, './bot/')
import utility
import exceptions
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from requests.exceptions import ReadTimeout
import re
import traceback
from datetime import datetime, time, date


def run():
    config = utility.load_config()
    vk_session = VkApi(token=config["token"])
    vk_api = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, config["group_id"])
    try:
        for event in longpoll.listen():
            try:
                if event.type == VkBotEventType.MESSAGE_NEW:
               #Слушаем longpoll, если пришло сообщение то:
                    if (event.raw["object"]["text"].startswith("!")):
                        text = re.match(r"(\W\w+)(.*)", event.raw["object"]["text"], flags = re.DOTALL)
                        command = text.group(1).strip()
                        message = text.group(2).strip()
                        handler = None
                        if event.from_user and str(event.raw["object"]["from_id"]) in config["admin_ids"]:
                            handler = utility.admin_commands.get(command.lower())
                        if not handler:
                            handler = utility.public_commands.get(command.lower())
                        if handler:
                            attachment = utility.parse_attachment(event)
                            result = handler.exec(message, attachment)
                            for msg in result:
                                utility.send_msg(vk_api, event, msg[0], msg[1])
                        else:
                            utility.send_msg(vk_api, event, "Ошибка: команда %s не найдена. \
                            Воспользуйтесь !помощь для получения списка команд" % command)
            except exceptions.BaseException as e:
                e.resolve(vk_api, event)
            except Exception as e:
                try:
                    with open("./log/unhandled_errors.log", mode="a") as log:
                        log.write(str(datetime.now()) + '\n')
                        log.write(traceback.format_exc())
                        log.write(str(e) + '\n')
                except OSError:
                    print("Error occured while opening log file")

    except ReadTimeout:
        run()

if __name__ == "__main__":
    run()

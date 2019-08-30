# coding=utf-8
import handlers
import exceptions
from datetime import datetime, time, date, timedelta, timezone
from vk_api.utils import get_random_id
from openpyxl import load_workbook
import re
import json

public_commands = {
    '!помощь' : handlers.PrintHelp(),
    '!расписание' : handlers.Schedule(),
    '!сейчас' : handlers.Now(),
    '!предметы' : handlers.Subjects(),
    '!инфо' : handlers.Info(),
}

admin_commands = {
    '!помощь' : handlers.PrintHelp(admin=True),
    '!расписание_добавить' : handlers.ScheduleAdd(),
    '!расписание_удалить' : handlers.ScheduleDelete(),
    '!расписание_перенести' : handlers.ScheduleMove(),
    '!расписание_аудитория' : handlers.ScheduleUpdate(),
    '!инфо_добавить' : handlers.InfoAdd(),
    '!инфо_удалить' : handlers.InfoDelete(),
    '!инфо_перенести' : handlers.InfoMove(),
    '!инфо_обновить' : handlers.InfoUpdate(),
}

aliases = {
    'вчера' : datetime.now(timezone(timedelta(hours=3))).date() - timedelta(1),
    'сегодня' : datetime.now(timezone(timedelta(hours=3))).date(),
    'завтра' : datetime.now(timezone(timedelta(hours=3))).date() + timedelta(1),
    '-' : datetime.now(timezone(timedelta(hours=3))).date() + timedelta(90),
}

weekdays = ["Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье"
]

timetable = [ (time(8,30), time(10,0)),
              (time(10,10), time(11,40)),
              (time(12,20), time(13,50)),
              (time(14,0), time(15,30)),
              (time(15,55), time(17,25)),
              (time(17,35), time(19,5)),
              (time(19,15), time(20,45)),
]

def send_msg(vk_api, event, response, attachment=""):
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

def parse_attachment(event):
    attachments = []
    for a in event.raw["object"]["attachments"]:
        type = a["type"]
        owner_id = a[type]["owner_id"]
        media_id = a[type]["id"]
        access_key = a[type]["access_key"]
        attachments.append("{}{}_{}_{}".format(type, owner_id, media_id, access_key))
    return ','.join(attachments)

def parse_date(str):
    try:
        date = aliases.get(str)
        if (not date):
            date = datetime.strptime(str, "%d.%m.%y").date()
    except ValueError:
        raise exceptions.DateFormatError()
    return date

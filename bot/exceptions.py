# coding=utf-8
import utility

class NikolayException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def resolve(self, vk_api, event):
        utility.send_msg(vk_api, event, self.msg)

class NotEnoughArgs(NikolayException):
    def __init__(self, min, got, msg=""):
        self.min = min
        self.got = got
        self.msg = msg
    def resolve(self, vk_api, event):
        response = self.msg + "Недостаточно параметров.\n \
        Ожидалось не менее %d, получено %d\n" % (self.min, self.got)
        utility.send_msg(vk_api, event, response)

class TooManyArgs(NikolayException):
    def __init__(self, max, got, msg=""):
        self.max = max
        self.got = got
        self.msg = msg
    def resolve(self, vk_api, event):
        response = self.msg + "Слишком много параметров.\n \
        Ожидалось не более %d, получено %d\n" % (self.max, self.got)
        utility.send_msg(vk_api, event, response)

class DateFormatError(NikolayException):
    def __init__(self, msg=""):
        self.msg = msg + "Не могу распознать дату. Пожалуйста, используйте формат дд.мм.гг\n"

class NumFormatError(NikolayException):
    def __init__(self, msg=""):
        self.msg = msg + "Пожалуйста введите число\n"

class NumOutOfRange(NikolayException):
    def __init__(self, min, max, msg=""):
        self.min = min
        self.max = max
        self.msg = msg
    def resolve(self, vk_api, event):
        response = self.msg + "Ожидалось число от %d до %d\n" % (self.min, self.max)
        utility.send_msg(vk_api, event, response)

class CellError(NikolayException):
    def __init__(self, date, num, msg=""):
        self.date = date
        self.num = num
        self.msg = msg
    def resolve(self, vk_api, event):
        response = "Возникла проблема с %s-ой парой %s: " % (self.num, self.date) + self.msg
        utility.send_msg(vk_api, event, response)

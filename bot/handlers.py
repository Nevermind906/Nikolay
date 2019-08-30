# coding=utf-8
import utility
import exceptions
import excel
import re
from datetime import datetime, time, date, timezone, timedelta

class Handler():
    def __init__(self):
        self.args = []

    def exec(self, message, attachment):
        self.parse_args(message)
        return [(message, attachment)]

    def check_args(self, min, max):
        if len(self.args) < min:
            raise exceptions.NotEnoughArgs(min, len(self.args))
        if len(self.args) > max:
            raise exceptions.TooManyArgs(max, len(self.args))

    def parse_args(self, message):
        if message: self.args = [s.strip() for s in message.split(",")]

class PrintHelp(Handler):
    """\
    !помощь [!команда] - вывод информации по доступным командам
    """
    def __init__(self, admin=False):
        super().__init__()
        self.admin = admin

    def parse_args(self, message):
        super().parse_args(message)
        if self.admin:
            self.commands = {**utility.public_commands, **utility.admin_commands}
        else:
            self.commands = utility.public_commands

    def exec(self, message, attachment):
        self.parse_args(message)
        self.check_args(0, 1)
        response = ""
        if len(self.args) == 1:
            try:
                result = self.commands[self.args[0]]
                response = response + result.__doc__ + '\n'
            except KeyError:
                raise BaseException("Я не смог найти команду %s. Воспользуйтесь\
                 !помощь для получения списка команд" % self.args[0])
        else:
            response = "Список команд:\n"
            for k in self.commands.keys():
                response = response + k + '\n'
        return [(response, "")]

class Schedule(Handler):
    """\
    !расписание [начальный день], [количество дней] - вывод актуального расписания.
    параметры отделяются ;
    [начальный день] - день, с которого начинается отсчет, в формате [сегодня|завтра|дд.мм.гг]
    [количество дней] - положительное число от 1 до 14 (по умолчанию 1)
    """
    def exec(self, message, attachment):
        self.parse_args(message)
        self.check_args(1, 2)
        eio = excel.ExcelIO()
        date = utility.parse_date(self.args[0])
        if len(self.args) == 1:
            delta = 1
        else:
            try:
                delta = int(self.args[1])
                if delta < 1 or delta > 14:
                    raise exceptions.NumOutOfRange(1, 14, "Ошибка во втором параметре. ")
            except ValueError:
                raise exceptions.NumFormatError("Ошибка во втором параметре. ")
        return [(eio.get_schedule(date, delta), "")]

class ScheduleChange(Handler):
    def _clear_cell(self, eio, date, num):
        cell_value = eio.schedule_read(date, num)
        if not cell_value:
            raise exceptions.CellError(date, num, "пара пустая")
        s = cell_value
        eio.schedule_write(date, num, "")
        return s

    def _write_cell(self, eio, date, num, message):
        cell_value = eio.schedule_read(date, num)
        if cell_value:
            raise exceptions.CellError(date, num, "пара уже занята")
        eio.schedule_write(date, num, message)

class ScheduleAdd(ScheduleChange):
    """\
    !расписание_добавить [дата], [номер пары], [предмет], [аудитория], [описание] \
    - добавить пару в расписание.
    [дата] - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    [номер пары] - число от 1 до 7
    [предмет] - название предмета
    [аудитория] - строка с номером аудитории
    [описание] - произвольная строка (необязательный параметр)
    """
    def parse_args(self, message):
        super().parse_args(message)
        if len(self.args) < 4:
            raise exceptions.NotEnoughArgs(4, len(self.args))
        if len(self.args) >= 5:
            self.description = ", " + ", ".join(self.args[4:])
        else:
            self.description = ""

    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        self.parse_args(message)
        self._write_cell(eio, self.args[0], self.args[1], self.args[2] + self.description + ", " + self.args[3])
        eio.save()
        return [("Пара успешно добавлена", "")]

class ScheduleDelete(ScheduleChange):
    """\
    !расписание_удалить [дата], [номер пары] - удалить пару из расписания.
    [дата] - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    [номер пары] - число от 1 до 7
    """
    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        self.parse_args(message)
        self.check_args(2, 2)
        self._clear_cell(eio, self.args[0], self.args[1])
        eio.save()
        return [("Пара успешно удалена", "")]

class ScheduleMove(ScheduleChange):
    """
    !расписание_перенести [дата], [номер пары], [новая дата], [новый номер пары] - перенос пары \
    на указанную дату.
    [дата] - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    [номер пары] - число от 1 до 7
    [новая дата] и [новый номер пары] - аналогично
    """
    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        self.parse_args(message)
        self.check_args(4, 4)
        old_cell = self._clear_cell(eio, self.args[0], self.args[1])
        self._write_cell(eio, self.args[2], self.args[3], old_cell)
        eio.save()
        return [("Пара успешно перенесена", "")]


class ScheduleUpdate(ScheduleChange):
    """\
    !расписание_аудитория [дата], [номер пары], [новый номер аудитории] - изменить номер аудитории.
    [дата] - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    [номер пары] - число от 1 до 7
    [новая аудитория] - строка с номером аудитории
    """
    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        self.parse_args(message)
        self.check_args(3, 3)
        cell_value = self._clear_cell(eio, self.args[0], self.args[1])
        lst = cell_value.split(", ")
        if len(lst) < 2:
            raise exceptions.BaseException("Что-то не так с ячейкой в файле расписания")
        lst[-1] = self.args[2]
        cell_value = ", ".join(lst)
        self._write_cell(eio, self.args[0], self.args[1], cell_value)
        eio.save()
        return [("Пара успешно обновлена", "")]

class Subjects(Handler):
    """\
    !предметы - вывод списка предметов и ведущих преподавателей.
    """
    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        subj_lst = eio.get_subjects()
        return [('Список предметов:\n' + '\n'.join(subj_lst), "")]

class Now(Handler):
    """\
    !сейчас - какая пара идет в данный момент.
    """
    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        dt = datetime.now(timezone(timedelta(hours=3)))
        t = dt.time()
        daily = eio.get_schedule(dt.date())
        daily_lst = daily.split("\n")
        response = ""
        if "Выходной, отдыхаем" in daily:
            response = "Пары закончились, отдыхаем"
        else:
            start = int(daily_lst[1][0])
            end = int(daily_lst[-3][0])
            if  t < utility.timetable[start-1][0] or t > utility.timetable[end-1][1]:
                response = "Пары закончились, отдыхаем"
            else:
                for i in range(start-1, end):
                    if t > utility.timetable[i][0] and t < utility.timetable[i][1]:
                        response = daily_lst[i-start+2]
                if response == "":
                    response = "Перерыв"
        return [(response, "")]

class Info(Handler):
    """
    команда может использоваться в 3-х вариантах:
    !инфо - получение всей актуальной информации
    !инфо [запрос] - получение актуальной информации по запросу
    !инфо -архив [запрос] - получение информации за все время
    """
    def parse_args(self, message):
        if message.startswith("-архив"):
            self.archive = True
            self.q = message.replace("-архив", "").strip()
            if not self.q:
                raise exceptions.BaseException('Пожалуйста, введите запрос')
            self.date = datetime.fromtimestamp(0).date()
        else:
            self.archive = False
            self.q = message
            self.date = datetime.now(timezone(timedelta(hours=3))).date()

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        return eio.get_info(self.q, self.date)


class InfoAdd(Handler):
    """
    !инфо_добавить [дата]
    [текст сообщения с новой строки]
    Внимание! Прикрепляя к сообщению документы убедитесь,
    что они были загружены как публичные (Учебный документ, Книга или Другой документ)
    [дата] - дедлайн для данного сообщения в формате [сегодня|завтра|дд.мм.гг]
    или [-],  если не хотите указывать конкретную дату (в качестве даты будет принят конец семестра)
    """
    def parse_args(self, message):
        self.message = ""
        if message:
            m = message.split("\n")
            self.date = utility.parse_date(m[0].strip())
            self.message = "\n".join(m[1:])
        else:
            raise exceptions.NotEnoughArgs(2, 0)
        if not self.message:
            raise exceptions.BaseException("Пожалуйста, введите текст сообщения")

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        dt = datetime.now(timezone(timedelta(hours=3)))
        eio.info_write(dt.date(), self.date, self.message, attachment)
        eio.save()
        return [("Сообщение успешно добавлено", "")]

class InfoDelete(Handler):
    """
    !инфо_удалить [id] - удалить сообщение
    [id]
    """
    def parse_args(self, message):
        super().parse_args(message)
        try:
            self.id = int(self.args[0])
        except ValueError:
            raise BaseException("Не могу распознать id")
    def exec(self, message, attachment):
        self.parse_args(message)
        self.check_args(1, 1)
        eio = excel.ExcelIO()
        eio.info_delete(self.id)
        eio.save()
        return [("Сообщение успешно удалено", "")]


class InfoUpdate(Handler):
    """
    !инфо_обновить [id] - обновить текст и прикрепления сообщение
    [текст сообщения с новой строки]
    [id] - уникальный идентификатор сообщения. Отображается при выводе !инфо
    """
    def parse_args(self, message, attachment):
        self.message = ""
        if message:
            try:
                m = message.split("\n")
                self.id = int(m[0].strip())
                self.message = "\n".join(m[1:])
                if not self.message and not attachment:
                    raise exceptions.BaseException("Пожалуйста, заполните сообщение")
            except ValueError:
                raise BaseException("Не могу распознать id")
        else:
            raise exceptions.NotEnoughArgs(2, 0)

    def exec(self, message, attachment):
        self.parse_args(message, attachment)
        eio = excel.ExcelIO()
        dt = datetime.now(timezone(timedelta(hours=3)))
        info = eio.info_read(self.id)
        if self.message:
            info[3] = self.message
        if attachment:
            info[4] = attachment
        eio.info_write(info[1], info[2], info[3], info[4], info[0])
        eio.save()
        return [("Сообщение успешно обновлено", "")]

class InfoMove(Handler):
    """
    !инфо_перенести [id], [новая дата] - изменить дедлайн сообщения
    [id] - уникальный идентификатор сообщения. Отображается при выводе !инфо
    [новая дата] - дата в формате [сегодня|завтра|дд.мм.гг]
    """
    def parse_args(self, message):
        super().parse_args(message)
        self.check_args(2, 2)
        try:
            self.id = int(self.args[0])
        except ValueError:
            raise BaseException("Не могу распознать id")
        self.date = utility.parse_date(self.args[1])

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        info = eio.info_read(self.id)
        eio.info_write(info[1], self.date, info[3], info[4], info[0])
        eio.save()
        return [("Сообщение успешно перенесено", "")]

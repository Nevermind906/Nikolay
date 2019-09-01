# coding=utf-8
import utility
import exceptions
import excel
from datetime import datetime, time, date, timezone, timedelta

class Handler():
    def __init__(self):
        self.args = []
        self.min_args = 0
        self.max_args = 0

    def exec(self, message, attachment):
        self.parse_args(message)
        return [(message, attachment)]

    def check_args(self):
        if len(self.args) < self.min_args:
            raise exceptions.NotEnoughArgs(self.min_args, len(self.args))
        if len(self.args) > self.max_args:
            raise exceptions.TooManyArgs(self.max_args, len(self.args))

    def parse_args(self, message):
        if message:
            self.args = [s.strip() for s in message.split(",")]
        else:
            self.args = []

class PrintHelp(Handler):
    """\
    !помощь [!команда] - вывод информации по доступным командам
    """
    def __init__(self, admin=False):
        self.admin = admin
        self.min_args = 0
        self.max_args = 1

    def parse_args(self, message):
        super().parse_args(message)
        self.check_args()
        if self.admin:
            self.commands = {**utility.public_commands, **utility.admin_commands}
        else:
            self.commands = utility.public_commands

    def exec(self, message, attachment):
        self.parse_args(message)
        response = ""
        if len(self.args) == 1:
            try:
                result = self.commands[self.args[0]]
                response = response + result.__doc__ + '\n'
            except KeyError:
                raise exceptions.NikolayException("Я не смог найти команду %s. \n\
                Воспользуйтесь !помощь для получения списка команд" % self.args[0])
        else:
            response = "Список команд:\n"
            for k in self.commands.keys():
                response = response + k + '\n'
        return [(response, "")]

class ScheduleShow(Handler):
    """\
    !расписание начальный день, [количество дней] - вывод актуального расписания.
    начальный день - день, с которого начинается отсчет, в формате [сегодня|завтра|дд.мм.гг]
    [количество дней] - положительное число от 1 до 14 (по умолчанию 1)
    """
    def __init__(self):
        self.min_args = 1
        self.max_args = 2

    def parse_args(self, message):
        super().parse_args(message)
        self.check_args()
        self.date = utility.parse_date(self.args[0])
        try:
            self.delta = int(self.args[1])
        except ValueError:
            raise exceptions.NumFormatError("Не могу распознать второй параметр. ")
        except IndexError:
            self.delta = 1
        if self.delta < 1 or self.delta > 14:
            raise exceptions.NumOutOfRange(1, 14)

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        return [(eio.get_schedule(self.date, self.delta), "")]

class ScheduleBase(Handler):
    def parse_args(self, message):
        super().parse_args(message)
        self.check_args()
        self.date = utility.parse_date(self.args[0])
        try:
            self.num = int(self.args[1])
        except ValueError:
            raise exceptions.NumFormatError("Не могу распознать второй параметр. ")

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


class ScheduleAdd(ScheduleBase):
    """\
    !расписание_добавить дата, номер пары, предмет, аудитория, [описание] \
    - добавить пару в расписание.
    дата - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    номер пары - число от 1 до 7
    предмет - название предмета
    аудитория - строка с номером аудитории
    [описание] - произвольная строка (необязательный параметр)
    """
    def __init__(self):
        self.min_args = 4
        self.max_args = 100

    def parse_args(self, message):
        super().parse_args(message)
        if self.num > 7 or self.num < 1:
            raise excepttions.NumOutOfRange(1, 7)
        self.subject = self.args[2]
        self.classroom = self.args[3]
        if len(self.args) >= 5:
            self.description = ", " + ", ".join(self.args[4:])
        else:
            self.description = ""

    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        self.parse_args(message)
        self._write_cell(eio, self.date, self.num, self.subject \
                        + self.description + ", " + self.classroom)
        eio.save()
        return [("Пара успешно добавлена", "")]

class ScheduleDelete(ScheduleBase):
    """\
    !расписание_удалить дата, номер пары - удалить пару из расписания.
    дата - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    номер пары - число от 1 до 7
    """
    def __init__(self):
        self.min_args = 2
        self.max_args = 2

    def parse_args(self, message):
        super().parse_args(message)
        if self.num > 7 or self.num < 1:
            raise excepttions.NumOutOfRange(1, 7)

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        self._clear_cell(eio, self.date, self.num)
        eio.save()
        return [("Пара успешно удалена", "")]

class ScheduleMove(ScheduleBase):
    """
    !расписание_перенести дата, номер пары, новая дата, новый номер пары - перенос пары \
    на указанную дату.
    дата - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    номер пары - число от 1 до 7
    новая дата и новый номер пары - аналогично
    """
    def __init__(self):
        self.min_args = 4
        self.max_args = 4

    def parse_args(self, message):
        super().parse_args(message)
        self.new_date = utility.parse_date(self.args[2])
        try:
            self.new_num = int(self.args[3])
        except ValueError:
            raise exceptions.NumFormatError("Не могу распознать второй параметр. ")
        if not 0 < self.num < 8 or not 0 < self.new_num < 8:
            raise excepttions.NumOutOfRange(1, 7)

    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        self.parse_args(message)
        old_cell = self._clear_cell(eio, self.date, self.num)
        self._write_cell(eio, self.new_date, self.new_num, old_cell)
        eio.save()
        return [("Пара успешно перенесена", "")]


class ScheduleUpdate(ScheduleBase):
    """\
    !расписание_аудитория дата, номер пары, новый номер аудитории - изменить номер аудитории.
    дата - дата проведения в формате [сегодня|завтра|дд.мм.гг]
    номер пары - число от 1 до 7
    новая аудитория - строка с номером аудитории
    """
    def __init__(self):
        self.min_args = 3
        self.max_args = 3

    def parse_args(self, message):
        super().parse_args(message)
        if self.num > 7 or self.num < 1:
            raise excepttions.NumOutOfRange(1, 7)
        self.classroom = self.args[2]

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        cell_value = self._clear_cell(eio, self.date, self.num)
        lst = cell_value.split(", ")
        if len(lst) < 2:
            raise exceptions.NikolayException("Что-то не так с ячейкой в файле расписания")
        lst[-1] = self.classroom
        cell_value = ", ".join(lst)
        self._write_cell(eio, self.date, self.num, cell_value)
        eio.save()
        return [("Пара успешно обновлена", "")]

class Subjects(Handler):
    """\
    !предметы - вывод списка предметов и ведущих преподавателей
    """
    def exec(self, message, attachment):
        eio = excel.ExcelIO()
        subj_lst = eio.get_subjects()
        return [('Список предметов:\n' + '\n'.join(subj_lst), "")]

class Now(Handler):
    """\
    !сейчас - следующая пара
    """
    def exec(self, message, attachment):
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
            if  t > utility.timetable[end][1]:
                response = "Пары закончились, отдыхаем"
            else:
                for i in range(start-1, end):
                    if t > utility.timetable[i][1] and t < utility.timetable[i+1][1]:
                        response = daily_lst[i-start+2]
        return [(response, "")]

class Info(Handler):
    """
    команда может использоваться в 3-х вариантах:
    !инфо - получение всей актуальной информации
    !инфо [запрос] - получение актуальной информации по запросу
    !инфо -архив запрос - получение информации за все время
    """
    def parse_args(self, message):
        if message.startswith("-архив"):
            self.archive = True
            self.q = message.replace("-архив", "").strip()
            if not self.q:
                raise exceptions.NikolayException('Пожалуйста, введите запрос')
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
    !инфо_добавить дата
    [текст сообщения с новой строки]
    Внимание! Прикрепляя к сообщению документы убедитесь,
    что они были загружены как публичные (Учебный документ, Книга или Другой документ)
    дата - дедлайн для данного сообщения в формате [сегодня|завтра|дд.мм.гг]
    или [-],  если не хотите указывать конкретную дату (+ 90 дней от текущего)
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
            raise exceptions.NikolayException("Пожалуйста, введите текст сообщения")

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        dt = datetime.now(timezone(timedelta(hours=3)))
        eio.info_write(dt.date(), self.date, self.message, attachment)
        eio.save()
        return [("Сообщение успешно добавлено", "")]

class InfoDelete(Handler):
    """
    !инфо_удалить id - удалить сообщение.
    id - номер строки с сообщением в таблице  (> 2)
    (отображается при выводе !инфо)
    """
    def __init__(self):
        self.min_args = 1
        self.max_args = 1

    def parse_args(self, message):
        super().parse_args(message)
        self.check_args()
        try:
            self.id = int(self.args[0])
            if self.id < 2:
                raise exceptions.NikolayException("Введите id > 2")
        except ValueError:
            raise exceptions.NumFormatError("Не могу распознать id. ")

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        eio.info_delete(self.id)
        eio.save()
        return [("Сообщение успешно удалено", "")]


class InfoUpdate(Handler):
    """
    !инфо_обновить id - обновить текст и прикрепления сообщения.
    [текст сообщения с новой строки]
    id - номер строки с сообщением в таблице  (> 2)
    (отображается при выводе !инфо)
    Текст оригинального сообщения не изменится, если вы оставите его пустым.
    Аналогично для прикреплений
    """
    def parse_args(self, message, attachment):
        self.message = ""
        if message:
            try:
                m = message.split("\n")
                self.id = int(m[0].strip())
                if self.id < 2:
                    raise exceptions.NikolayException("Введите id > 2")
                self.message = "\n".join(m[1:])
                if not self.message and not attachment:
                    raise exceptions.NikolayException("Пожалуйста, заполните сообщение")
            except ValueError:
                raise exceptions.NumFormatError("Не могу распознать id. ")
        else:
            raise exceptions.NotEnoughArgs(2, 0)

    def exec(self, message, attachment):
        self.parse_args(message, attachment)
        eio = excel.ExcelIO()
        dt = datetime.now(timezone(timedelta(hours=3)))
        info = eio.info_read(self.id)
        if not info[1]:
            raise exceptions.NikolayException('Не удалось найти сообщение с id=%d' % self.id)
        if self.message:
            info[3] = self.message
        if attachment:
            info[4] = attachment
        eio.info_write(info[1], info[2], info[3], info[4], info[0])
        eio.save()
        return [("Сообщение успешно обновлено", "")]

class InfoMove(Handler):
    """
    !инфо_перенести id, новая дата - изменить дедлайн сообщения
    id - номер строки с сообщением в таблице (> 2)
    (отображается при выводе !инфо)
    новая дата - дата в формате [сегодня|завтра|дд.мм.гг]
    """
    def __init__(self):
        self.min_args = 2
        self.max_args = 2

    def parse_args(self, message):
        super().parse_args(message)
        self.check_args()
        try:
            self.id = int(self.args[0])
        except ValueError:
            raise exceptions.NumFormatError("Не могу распознать id. ")
        if self.id < 2:
            raise exceptions.NikolayException("Введите id > 2")
        self.date = utility.parse_date(self.args[1])

    def exec(self, message, attachment):
        self.parse_args(message)
        eio = excel.ExcelIO()
        info = eio.info_read(self.id)
        if not info[1]:
            raise exceptions.NikolayException('Не удалось найти сообщение с id=%d' % self.id)
        eio.info_write(info[1], self.date, info[3], info[4], info[0])
        eio.save()
        return [("Сообщение успешно перенесено", "")]

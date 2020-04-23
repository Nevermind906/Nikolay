import markovify
import json

class Bot():

    def __init__(self, banned_genres=[]):
        self.banned_genres = banned_genres
        with open('data/data.json', encoding='utf-8') as f:
            data = json.load(f)
            text = ""
            for ff in data:
                text = text + ff["text"]
        self.model = markovify.Text(text)
        self.commands = {
            '!помощь' : self.print_help,
            '!го' : self.generate,
        }
        self.play_mode = False

    def responde(self, command, message):
        """\
        передает сообщение нужному обработчику
        """
        if command in self.commands:
            return self.commands[command](message)
        else:
            return ("Я не смог найти команду %s. \n\
                    Воспользуйтесь !помощь для получения списка команд" % command)

    def generate(self, message):
        """\
        !го - генерирует сообщение в соответствии с выбранными жанрами
        """
        return self.generate_message()

    def generate_message(self):
        """\
        генерирует короткое сообщение
        """
        response = ""
        while not response:
            response = self.model.make_short_sentence(200)
        return response

    def print_help(self, command):
        """\
        !помощь [!команда] - вывод информации по доступным командам
        """
        if command:
            if command in self.commands:
                return self.commands[command].__doc__ + '\n'
            else:
                return ("Я не смог найти команду %s. \n\
                        Воспользуйтесь !помощь для получения списка команд" % command)
        else:
            response = "Список команд:\n"
            for k in self.commands.keys():
                response = response + k + '\n'
            return response

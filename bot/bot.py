import markovify
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer # to perform bow
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import string
import numpy as np
from pymystem3 import Mystem
from nltk.corpus import stopwords # for stop words
from string import punctuation
import pandas as pd
from sklearn.metrics import pairwise_distances
import re
class Bot():

    def __init__(self):
        with open('data/data.json', encoding='utf-8') as f:
            data = json.load(f)
            text = ""
            for ff in data:
                text = text + ff["text"]
        self.model = markovify.Text(text)
        self.commands = {
            '!помощь' : self.print_help,
            '!го' : self.generate,
            '!ролка' : self.enable_play_mode
        }
        self.play_mode = False

    def responde(self, event):
        """\
        передает сообщение нужному обработчику
        """
        if self.play_mode:
            return self.generate_similar_sentence(event.raw["object"]["text"])
        else:
            text = re.match(r"(\W\w*)(.*)", event.raw["object"]["text"], flags = re.DOTALL)
            if text:
                command = text.group(1).strip()
                message = text.group(2).strip()
                if command in self.commands:
                    return self.commands[command](message)
                else:
                    return ("Я не смог найти команду %s. \n\
                            Воспользуйтесь !помощь для получения списка команд" % command)

    def enable_play_mode(self, message):
        """\
        !ролка - экспериментальная функция, бот будет пытаться сыграть с вами\
        в ролевую игру, отвечая на ваши сообщения. Генерация ответа может \
        занять некоторое время.
        """
        self.play_mode = True
        return "Ну чтож, давай поиграем, лапуля. Стоп-слово ты знаешь ;)"

    def generate(self, message):
        """\
        !го - генерирует сообщение в соответствии с выбранными жанрами
        """
        return self.generate_sentence()

    def generate_sentence(self):
        """\
        генерирует короткое сообщение
        """
        response = ""
        while not response:
            response = self.model.make_short_sentence(300)
        return response

    def generate_similar_sentence(self, message):
        """\
        генерирует короткое сообщение
        """
        if message.lower() == "я кончил" or message.lower() == "чотыре" :
            self.play_mode = False
            return "Приходи ещё, детка <3 "
        df = pd.read_csv("data/cache.csv")
        phrases = set()
        for i in range(2):
            p = ""
            while not p or p in df['phrases']:
                p = self.model.make_short_sentence(300)
            phrases.add(p)
        phrases = list(phrases)
        lemmas = []
        for p in phrases:
            lemmas.append(self.text_normalization(p))
        df1 = pd.DataFrame(list(zip(phrases, lemmas)), columns=["phrases", "lemmas"])
        df = df.append(df1)
        df.to_csv("data/cache.csv", index=False)
        cv = CountVectorizer() # intializing the count vectorizer
        X = cv.fit_transform(df["lemmas"]).toarray()
        features = cv.get_feature_names()
        df_bow = pd.DataFrame(X, columns = features)
        Question_lemma = self.text_normalization(message) # applying the function that we created for text normalizing
        Question_bow = cv.transform([Question_lemma]).toarray() # applying bow
        cosine_value = 1 - pairwise_distances(df_bow, Question_bow, metric = 'cosine' )
        if not np.sum(cosine_value):
            return ""
        else:
            index_value = cosine_value.argmax() # returns the index number of highest value
        return df["phrases"].array[index_value]

    def text_normalization(self, text):
        mystem = Mystem()
        russian_stopwords = stopwords.words("russian")
        tokens = mystem.lemmatize(text.lower())
        tokens = [token for token in tokens if token not in russian_stopwords\
                  and token != " " \
                  and token.strip() not in punctuation]

        text = " ".join(tokens)

        return text

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

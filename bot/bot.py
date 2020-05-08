import markovify
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer # to perform bow
from sklearn.metrics.pairwise import cosine_similarity
from gtts import gTTS
import nltk
import time
import string
from vk_api.upload import VkUpload
import numpy as np
from pymystem3 import Mystem
from nltk.corpus import stopwords # for stop words
from string import punctuation
import pandas as pd
from sklearn.metrics import pairwise_distances
import re
import os
import utility
class Bot():

    def __init__(self, vk_session):
        self.vk = vk_session.get_api()
        self.upload = VkUpload(vk_session)
        with open('data/data.json', encoding='utf-8') as f:
            data = json.load(f)
            text = ""
            for ff in data:
                text = text + ff["text"]
        self.model = markovify.Text(text)
        self.commands = {
            '!помощь' : self.print_help,
            '!го' : self.generate_voice,
            '!текст' : self.generate_sentence,
            '!ролка' : self.enable_play_mode
        }
        self.play_mode = False

    def uploadMP3onSERVER(self, text, event):
        tts = gTTS(text=text, lang="ru")
        name = str(int(time.time())) + ".mp3" # имя файла
        tts.save(name) # сохраняем файл
        #print(event.raw["object"]["from_id"])
        document = self.upload.audio_message(name, peer_id=event.raw["object"]["from_id"])
        #print(document)
        type = document["type"]
        att = type + str(document[type]["owner_id"]) + "_" + str(document[type]["id"]) + "_" + document[type]["access_key"]
        #print(att)
        #utility.send_msg(self.vk, event, "", att)
        os.remove(name)
        return att

    def responde(self, event):
        """\
        передает сообщение нужному обработчику
        """
        self.event = event
        if self.play_mode:
            msg = self.generate_similar_sentence(self.event.raw["object"]["text"])
            if msg:
                utility.send_msg(self.vk, self.event, msg)
        else:
            text = re.match(r"(\W\w*)(.*)", event.raw["object"]["text"], flags = re.DOTALL)
            if text:
                command = text.group(1).strip()
                message = text.group(2).strip()
                if command in self.commands:
                    msg, att = self.commands[command](message)
                    utility.send_msg(self.vk, self.event, msg, att)
                else:
                    msg = ("Я не смог найти команду %s. \n\
                            Воспользуйтесь !помощь для получения списка команд" % command)
                    utility.send_msg(self.vk, self.event, msg)

    def enable_play_mode(self, message):
        """\
        !ролка - экспериментальная функция, бот будет пытаться сыграть с вами\
        в ролевую игру, отвечая на ваши сообщения. Генерация ответа может \
        занять некоторое время.
        """
        self.play_mode = True
        return ("Ну чтож, давай поиграем, лапуля. Стоп-слово ты знаешь ;)", "")

    def generate_voice(self, message):
        """\
        !го - генерирует голосовое сообщение
        """
        text, _ = self.generate_sentence(message)
        att = self.uploadMP3onSERVER(text, self.event)
        return ("", att)

    def generate_sentence(self, message):
        """\
        !текст - генерирует текстовое сообщение
        """
        response = ""
        while not response:
            response = self.model.make_sentence()
        return (response, "")

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
                return (self.commands[command].__doc__ + '\n', "")
            else:
                return (("Я не смог найти команду %s. \n\
                        Воспользуйтесь !помощь для получения списка команд" % command), "")
        else:
            response = "Список команд:\n"
            for k in self.commands.keys():
                response = response + k + '\n'
            return (response, "")

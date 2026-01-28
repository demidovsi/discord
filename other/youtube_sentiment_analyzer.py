import os
import json
import time

import yt_dlp
import whisper
from transformers import pipeline
import glob

import config
import common
import  trafaret_thread
import cloud


# Добавьте эту строку в начало скрипта после импортов
os.environ["PATH"] += os.pathsep + r"ffmpeg/bin"

def transcribe_youtube_video(url):
    # Настройка загрузки только аудио
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'postprocessor_args': {
            'ffmpeg': ['-loglevel', 'quiet'],
        }
    }
    
    # Загрузка аудио
    # print("Загружаем аудио...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Найти созданный аудио файл
    audio_files = glob.glob("temp_audio.*")
    if not audio_files:
        raise FileNotFoundError("Аудио файл не найден")
    
    audio_file = audio_files[0]
    # print(f"Найден аудио файл: {audio_file}")
    
    # Загрузка модели Whisper для транскрибирования
    # print("Загружаем модель Whisper...")
    model = whisper.load_model("base")
    
    # Транскрибирование
    # print("Транскрибируем аудио...")
    result = model.transcribe(audio_file)
    
    # Удаление временного файла
    if os.path.exists(audio_file):
        os.remove(audio_file)
    
    return result["text"]

def analyze_sentiment_about_product(text, product_name="Urban Heat"):
    # Инициализация модели анализа настроения
    # print("Загружаем модель анализа настроения...")
    sentiment_analyzer = pipeline("sentiment-analysis", 
                                model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    
    # Поиск упоминаний продукта в тексте
    product_mentions = []
    sentences = text.split('.')
    
    for sentence in sentences:
        if product_name.lower() in sentence.lower():
            product_mentions.append(sentence.strip())
    
    if not product_mentions:
        err = f"Упоминания {product_name} не найдены в тексте."
        print(err)
        return None, err
    
    # Анализ настроения для каждого упоминания
    sentiments = []
    for mention in product_mentions:
        if mention:
            sentiment = sentiment_analyzer(mention)[0]
            sentiments.append({
                'text': mention,
                'sentiment': sentiment['label'],
                'score': sentiment['score']
            })
    
    return sentiments, None

def main():
    # url = "https://www.youtube.com/watch?v=pknx3Lu3few"
    # url = "https://www.youtube.com/watch?v=rCMhdn6dSO8"
    # url = "https://www.youtube.com/watch?v=bhMICVNFyHg"
    url = "https://www.youtube.com/watch?v=bhMICVNFyHg&pp=ygUTdXJiYW4gaGVhdCBnYW1lcGxheQ%3D%3D"

    print("Загрузка и транскрибирование видео...")
    transcript = transcribe_youtube_video(url)

    # Извлечение ID видео из URL для использования в имени файла
    video_id = url.split("watch?v=")[-1]
    # transcript_filename = f"transcript_{video_id}.txt"

    # Сохранение транскрипции в файл
    # try:
    #     with open(transcript_filename, "w", encoding="utf-8") as f:
    #         f.write(transcript)
    #     print(f"\nТранскрипция сохранена в файл: {transcript_filename}")
    # except Exception as e:
    #     print(f"\nОшибка при сохранении транскрипции: {e}")

    print(f"\nТранскрипт:\n{transcript}\n")

    print("Анализ настроения относительно Urban Heat...")
    sentiments, err = analyze_sentiment_about_product(transcript, "Urban Heat")

    if sentiments:
        print("\nРезультаты анализа настроения:")
        for i, sentiment in enumerate(sentiments, 1):
            print(f"{i}. Текст: {sentiment['text']}")
            print(f"   Настроение: {sentiment['sentiment']} (уверенность: {sentiment['score']:.2f})")
            print()

    # Общий анализ настроения всего текста
    overall_sentiment = pipeline("sentiment-analysis")(transcript[:512])[0]
    print(f"Общее настроение видео: {overall_sentiment['label']} ({overall_sentiment['score']:.2f})")



class YoutubeTranscript(trafaret_thread.TrafaretThread):
    count = 0  # общее количество прочитанных статей

    def __init__(self, source, code_function, code_period, description):
        super(YoutubeTranscript, self).__init__(source, code_function, code_period, description)

    def work(self):
        super(YoutubeTranscript, self).work()
        if common.get_value_config_param('active', self.par) != 1:
            return False
        # прочитать нужные для работы параметры
        # получить токен для записи в БД
        result = self.make_login()
        self.count = 0
        if result:
            common.write_log_db(
                'Start', self.source, 'Начало работы по оценке публикаций на youtube',
                file_name=common.get_computer_name(), token=self.token)
            # читаем не обработанные публикации
            ans, is_ok, _ = common.send_rest('v2/select/{schema}/nsi_list?where=need_reload&column_order=id'.format(schema=config.schema_name))
            if not is_ok:
                self.finish_text = 'Ошибка при получении списка публикаций для загрузки\n' + str(ans)
                return False
            ans = json.loads(ans)
            for data in ans:
                t0 = time.time()
                transcript = ''
                url = data['url']
                video_id = data['id']
                try:
                    # Получаем ID видео из URL
                    # print("Загрузка и транскрибирование видео...")
                    transcript = transcribe_youtube_video(url)
                    # print(f"\nТранскрипт:\n{transcript}\n")
                    # print("Анализ настроения относительно Urban Heat...")
                    sentiments, err = analyze_sentiment_about_product(transcript, "Urban Heat")

                    values = {"id": data['id'], "need_reload": 'false', 'size_file': len(transcript)}
                    if sentiments:
                        # Извлечение ID видео из URL для использования в имени файла
                        blob_name = f"transcript_{video_id}.txt"

                        # Общий анализ настроения всего текста
                        self.count += 1
                        overall_sentiment = pipeline("sentiment-analysis")(transcript[:512])[0]
                        values["sentiment"] = overall_sentiment['label']
                        values["value"] = overall_sentiment['score']
                        values['result'] = '%s'
                        values['err'] = ''
                        datas = json.dumps(sentiments, ensure_ascii=False)
                        print(f"Общее настроение видео: {overall_sentiment['label']} ({overall_sentiment['score']:.2f})")
                    else:
                        values['err'] = err
                        blob_name = f"no_transcript_{video_id}.txt"
                        datas = ''

                    # Сохранение транскрипции в облако
                    cloud.save_file_bucket(blob_name, transcript)
                    params = {
                        "schema_name": config.schema_name,
                        "object_code": "list",
                        "values": values,
                        "datas": datas
                    }
                    ans, is_ok, _ = common.send_rest('v2/entity', 'PUT',
                        params=params, token_user=self.token)

                    if not is_ok:
                        self.finish_text = 'Ошибка при  коррекции видео в БД\n' + str(ans)
                        return False
                    common.write_log_db('info', self.source,
                                        'Обработано видео: ' + str(data['id']) + ' ' + str(data['url']), page=data['id'],
                                        td=time.time() - t0, file_name=common.get_computer_name(), token=self.token)
                except Exception as er:
                    st = 'Ошибка при обработке видео\n' + str(er)
                    common.write_log_db('Exception', self.source, st + '\n' + data['url'], page=data['id'],
                                        td=time.time() - t0, file_name=common.get_computer_name(), token=self.token)
                    values = {"id": data['id'], "need_reload": 'false'}
                    values['err'] = '%s'
                    datas = f'{er}'
                    if transcript:
                        blob_name = f"error_transcript_{video_id}.txt"
                        # Сохранение транскрипции в облако
                        cloud.save_file_bucket(blob_name, transcript)
                        values['size_file'] = len(transcript)
                    params = {
                        "schema_name": config.schema_name,
                        "object_code": "list",
                        "values": values,
                        "datas": datas
                    }
                    ans, is_ok, _ = common.send_rest('v2/entity', 'PUT', params=params,
                                                     token_user=self.token)
                    if not is_ok:
                        self.finish_text = 'Ошибка при коррекции видео в БД\n' + str(ans)
                        return False

            self.finish_text = f'Обработано публикаций: {self.count}'
        return result

# if __name__ == "__main__":
#     main()

if __name__ == "__main__":
    YoutubeTranscript('YoutubeTranscript', 'youtube_transcript', 'period',
         "Поток 'Определение отношения из видео youtube' по игре URBAN HEAT").start()
    while True:
        time.sleep(5)

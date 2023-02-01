import requests
from aiogram.dispatcher import FSMContext
from io import BytesIO

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.utils.markdown import hcode


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        await state.finish()


async def translate(message, text, ya, Synthesize):
    detectedLanguage = await ya.detect(text)
    translatedText = None
    if detectedLanguage == 'en':
        translatedText = await ya.translate_text(text, 'ru', 'en')
    elif detectedLanguage == 'ru':
        translatedText = await ya.translate_text(text, 'en', 'ru')
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton('Озвучить', callback_data=translatedText))
    await message.answer(hcode(translatedText), parse_mode=ParseMode.HTML, reply_markup=markup)
    await Synthesize.textCall.set()


async def dictation_statistics(count, correct, incorrect):
    if count == 0:
        percents = 0
        mark = 'None'
    else:
        percents = round(correct / count * 100, 2)
        if percents >= 100:
            mark = '5'
        elif percents >= 95:
            mark = '5-'
        elif percents >= 90:
            mark = '4+'
        elif percents >= 80:
            mark = '4'
        elif percents >= 75:
            mark = '4-'
        elif percents >= 70:
            mark = '3+'
        elif percents >= 60:
            mark = '3'
        elif percents >= 55:
            mark = '3-'
        elif percents >= 50:
            mark = '2+'
        elif percents >= 40:
            mark = '2'
        elif percents >= 35:
            mark = '2-'
        elif percents >= 30:
            mark = '1+'
        elif percents >= 20:
            mark = '1'
        elif percents >= 15:
            mark = '1-'
        elif percents >= 10:
            mark = '0+'
        else:
            mark = '(⊙ˍ⊙)'
    return f'*Статистика:*\n_Всего_ - `{count}`\n_Правильных_ - `{correct}`\n_Неправильных_ - `{incorrect}`\n_Процент_ - `{percents}%`\n_Оценка_ - `{mark}`'


async def dict_transformation(dict_, order) -> dict:
    dict_ = dict_.split('\n')
    to_dictate = {}

    for line in dict_:
        k, v = line.split(' *** ', 1)
        if order:
            to_dictate[v] = k
        else:
            to_dictate[k] = v

    return to_dictate


class YandexTranslator:
    def __init__(self, folder_id, API_KEY):
        self.folder_id = folder_id
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {API_KEY}"
        }

    async def translate_text(self, text: str | list, targetLanguage: str, sourceLanguage: str = None) -> dict:
        body = {
            "texts": text,
            "folderId": self.folder_id,
            "targetLanguageCode": targetLanguage
        }
        if sourceLanguage is not None:
            body['sourceLanguageCode'] = sourceLanguage

        response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
                                 json=body,
                                 headers=self.headers
                                 )
        result = response.json()['translations']
        if isinstance(text, str):
            return result[0]['text']
        else:
            return result

    async def detect(self, text: str, languageCodeHints: list | tuple = ('en', 'ru')) -> str:
        body = {
            "folderId": self.folder_id,
            "text": text
        }

        if languageCodeHints is not None:
            body['languageCodeHints'] = languageCodeHints

        response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/detect',
                                 json=body,
                                 headers=self.headers
                                 )
        return response.json()['languageCode']

    async def auto_list_translation(self, to_translate: list, sourceLanguage=None) -> dict:
        l = []
        translationDict = {}

        if sourceLanguage is None:
            sourceLanguage = await self.detect(to_translate[0])

        targetLanguage = 'ru' if sourceLanguage == 'en' else 'en'
        translationList = (await self.translate_text(to_translate, targetLanguage))

        l.append([i['text'] for i in translationList])

        for i in range(len(to_translate)):
            translationDict[to_translate[i]] = translationList[i]['text']

        return translationDict

    async def synthesize(self, text: str, speed=1.0, language: str = 'en-US', voice: str = 'john',
                         emotion: str = 'neutral') -> BytesIO:
        if (language == 'ru-RU') and (voice == 'john'):
            voice = 'alena'
        elif language == 'en-US':
            speed = 0.9
        body = {
            "folderId": self.folder_id,
            "text": text,
            'lang': language,
            'voice': voice,
            'emotion': emotion,
            'speed': speed
        }
        headers = self.headers
        headers.pop('Content-Type', None)
        response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', data=body,
                                 headers=headers)
        return BytesIO(response.content)

    async def recognize(self, audio: BytesIO, language: str = 'ru-RU'):
        response = requests.post(
            f'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?folderId={self.folder_id}&lang={language}',
            headers=self.headers, data=audio).json()
        return response['result']

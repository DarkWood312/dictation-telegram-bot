import requests
from aiogram.dispatcher import FSMContext


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        await state.finish()


async def translate(text: str | list, target_language='ru', source_language='en', API_KEY='AQVNxfz109UVOMwPQzQr83ow1QbLbtdGRcyW7lGF', folder_id='b1gvvk7vrsehk1e13vum'):
    body = {
        "targetLanguageCode": target_language,
        "sourceLanguageCode": source_language,
        "texts": text,
        "folderId": folder_id,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }

    response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
                             json=body,
                             headers=headers
                             )
    return response.json()

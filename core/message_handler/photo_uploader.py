import asyncio
import os
from pathlib import Path

import requests
from vk_api.upload import FilesOpener

BASE_DIR = Path(__file__).parent.parent.parent
IMAGE_DIR = Path(BASE_DIR, 'config/image')


class PhotoUploader:

    def __init__(self, overlord):
        self.overlord = overlord
        self.http = requests.Session()
        self.http.headers.pop('user-agent')
        self.photos = {}

    async def uploaded_photo_from_dir(self) -> dict:
        """Выгрузка всех фото из config/image в базу в vk для текущего пользователя"""

        dir_photos = list(os.walk(IMAGE_DIR))[0][2]
        url_photos = await self.uploaded_photo(*dir_photos)
        photos_attachments = [f'photo{ph["owner_id"]}_{ph["id"]}' for ph in url_photos]
        res = dict(zip(dir_photos, photos_attachments))
        self.photos = res
        return res

    async def uploaded_photo(self, *images: str):
        """Выгрузка своего фото на сервер"""

        photos = [str(Path(IMAGE_DIR, im)) for im in images]
        album = await self.overlord.api('photos.getMessagesUploadServer')
        url = album['upload_url']
        with FilesOpener(photos) as photo_files:
            response = self.http.post(url, files=photo_files)
        photos = await self.overlord.api('photos.saveMessagesPhoto', **response.json())
        return [{'id': im['id'], 'owner_id': im['owner_id'], 'access_key': im['access_key']} for im in photos]


async def main():
    from queue import Queue

    from core.handlers.log_message import LogMessage
    from settings import tg_id, tg_token, vk_tokens
    from vk_bot import AdminAccount
    thread_log_collector = Queue()
    acc_log_message = LogMessage(thread_log_collector)
    vk = AdminAccount(vk_tokens[0], tg_token, tg_id, acc_log_message)
    ph = PhotoUploader(vk)
    await  ph.uploaded_photo_from_dir()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # asyncio.run(main())


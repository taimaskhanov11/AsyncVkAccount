import os
from pathlib import Path

import requests
from vk_api.upload import FilesOpener

BASE_DIR = Path(__file__).parent.parent.parent
IMAGE_DIR = Path(BASE_DIR, 'config/image')


class PhotoUploader:

    def __init__(self):
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

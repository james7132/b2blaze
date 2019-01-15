from aiob2.api import BASE_URL, API_VERSION, API
from aiob2.exceptions import B2AuthorizationError
from aiob2.exceptions import B2Exception
from aiob2.exceptions import B2InvalidRequestType
from aiob2.utilities import StreamWithHashProgress
from aiob2.utilities import get_content_length
from aiob2.utilities import url_encode
from hashlib import sha1
from io import BytesIO
import aiohttp
import datetime
import sys


async def get_json(response):
    if response.status != 200:
        raise await B2Exception.parse(response)
    return await response.json()


class B2Connector():
    """

    """

    def __init__(self, session):
        """

        :param key_id:
        :param application_key:
        """
        self.session = session
        self.key_id = None
        self.application_key = None
        self.account_id = None
        self.auth_token = None
        self.authorized_at = None
        self.api_url = None
        self.download_url = None
        self.recommended_part_size = None
        #TODO:  Part Size

    async def is_authorized(self):
        """

        :return:
        """
        if self.auth_token is None:
            return False
        time_authorized = datetime.datetime.utcnow() - self.authorized_at
        if time_authorized > datetime.timedelta(hours=23):
            await self._authorize()
        return True

    async def _authorize(self, key_id, application_key):
        self.key_id = key_id
        self.application_key = application_key

        path = BASE_URL + API.authorize

        auth = aiohttp.BasicAuth(self.key_id, self.application_key)
        async with self.session.get(path, auth=auth) as response:
            response_json = await get_json(response)
        self.authorized_at = datetime.datetime.utcnow()
        self.account_id = response_json['accountId']
        self.auth_token = response_json['authorizationToken']
        self.api_url = response_json['apiUrl'] + API_VERSION
        self.download_url = response_json['downloadUrl'] + \
            API_VERSION + API.download_file_by_id
        self.recommended_part_size = response_json['recommendedPartSize']

    async def get(self, path, headers={}):
        if not self.authorized:
            raise B2AuthorizationError('Not authorized.')
        url = self.api_url + path
        headers.update({'Authorization': self.auth_token})
        async with self.session.get(url, headers=headers) as response:
            return await get_json(response)

    async def put(self, path, headers={}, params={},
                  account_id_required=False):
        if not self.authorized:
            raise B2AuthorizationError('Not authorized.')
        url = self.api_url + path
        headers.update({'Authorization': self.auth_token})
        if account_id_required:
            params.update({'accountId': self.account_id})
        headers.update({'Content-Type': 'application/json'})
        async with self.session.post(url, json=params, headers=headers) as response:
            return await get_json(response)

    async def upload_file(self, file_contents,
                          file_name,
                          mime_content_type=None,
                          content_length=None):
        if hasattr(file_contents, 'read'):
            content_length = content_length or get_content_length(
                file_contents)
        else:
            content_length = content_length or len(file_contents)

        hasher, stream = self._create_hasher_stream(file_contents)
        content_length += hasher.digest_size

        upload_url, token = await self._upload_url()

        headers = {
            'Content-Type': mime_content_type or 'b2/x-auto',
            'Content-Length': str(content_length),
            'X-Bz-Content-Sha1': 'hex_digits_at_end',
            'X-Bz-File-Name': url_encode(file_name),
            'Authorization': token
        }

        async with self.session.post(upload_url, headers=headers,
                                     data=stream) as response:
            return await get_json(response)

    async def upload_part(self, file_contents, part_number):
        hasher, stream = self._create_hasher_stream(file_contents)
        content_length = len(file_contents) + hasher.digest_size * 2

        upload_url, token = await self._upload_url()

        headers = {
            'Content-Length': str(content_length),
            'X-Bz-Content-Sha1': 'hex_digits_at_end',
            'X-Bz-Part-Number': str(part_number),
            'Authorization': token
        }

        async with self.session.post(upload_url, headers=headers,
                                     data=stream) as response:
            return await get_json(response)

    def download_file(self, file_id):
        headers = {'Authorization': self.auth_token}
        return self.session.get(self.download_url,
                                headers=headers,
                                params={'fileId': file_id})

    async def _upload_url(self):
        response = await self.post(path=API.upload_url,
                                   params={'bucketId': self.id})
        return (response.get('uploadUrl', None),
                response.get('authorizationToken', None))

    def _create_hasher_stream(self, file_contents):
        if not hasattr(file_contents, 'read'):
            file_contents = BytesIO(file_cotents)

        hasher = sha1()

        def update_block(block):
            hasher.update(block)

        async def data_stream():
            loop = asyncio.get_running_loop()
            for chunk in iter(lambda: file_contents.read(1024 ** 2), b''):
                await loop.run_in_executor(None, update_hash, chunk)
                yield chunk
            yield hasher.hexdigest().encode()

        return hasher, data_stream()

from aiob2.exceptions import B2Exception, B2BucketDeleted
from aiob2.api import API


MAX_FILES_PER_LIST = 10000


def _chunk_file(path, chunk_size):
    with open(contents.name, 'rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            yield chunk


def _sanitize_file_name(file_name):
    if file_name[0] == '/':
        return file_name[1:]
    return file_name


class B2Bucket(object):

    def __init__(self, parent, json):
        self.connector = parent.connector
        self.deleted = False

        self.id = json['bucketId']
        self.name = json['bucketName']
        self.type = json['bucketType']
        self.info = json['bucketInfo']
        self.lifecycle_rules = json['lifecycleRules']
        self.revision = json['revision']
        self.cors_rules = json['corsRules']

    async def delete(self):
        """ Delete the bucket.

        Calls: b2_delete_bucket
        """

        await self.connector.post(
            path=API.delete_bucket,
            account_id_required=True,
            params={'bucketId': self.id})

        self.deleted = True

    def edit(self):
        #TODO:  Edit details
        pass

    async def get_file(self, file_name=None, file_id=None):
        """ Get a file by file name or id.
            Required:
                file_name or file_id

            Parameters:
                file_name:          (str) File name
                file_id:            (str) File ID
        """
        if file_name is not None:
            return await self._get_by_name(file_name)
        elif file_id is not None:
            return await self._get_by_id(file_id)
        raise ValueError('file_name or file_id must be passed')

    async def _get_by_id(self, file_id):
        """ b2_get_file_info """
        return B2File(self, await self.connector.post(API.file_info,
                                                      params={'fileId': file_id}))

    async def _get_by_name(self, name):
        async for file in self.list_file(prefix=name):
            if file.name == name:
                return file
        raise B2FileNotFoundError('Filename {} not found'.format(file_name))

    async def list_files(self, prefix=None,
                         start_file=None,
                         limit=100,
                         delimiter=None):
        """ b2_list_file_names """
        params = {'bucketId': self.id}
        if prefix is not None:
            params['prefix'] = b2_url_encode(prefix)
        if start_file is not None:
            params['startFileName'] = start_file
        if limit is not None:
            params['maxFileCount'] = min(int(limit), MAX_FILES_PER_LIST)
        if delimiter is not None:
            params['delimiter'] = delimiter

        while True:
            response = await self.connector.post(API.list_all_files, params)

            for file_json in response['files']:
                yield B2File(self, file_json)

            if files_json['nextFileName'] is None:
                break
            params['startFileName'] = response['nextFileName']

    async def upload_file(self, contents, file_name, mime_content_type=None,
                          content_length=None):
        file_name = _sanitize_file_name(file_name)
        return B2File(self, await self._upload(
            endpoint=API.uppload_url,
            handler=self.connector.upload_file,
            contents=contents,
            file_name=file_name,
            content_length=content_length))

    async def upload_large_file(self, contents, file_name,
                                part_size=None,
                                mime_content_type=None, content_length=None):
        file_name = _sanitize_file_name(file_name)
        part_size = part_size or self.connector.recommended_part_size
        content_length = contennt_length or get_content_length(contents)

        file_id = self._start_file_upload(file_name, mime_content_type)
        sha_list = self._upload_file_parts(file_id)
        response = self._finish_large_file(file_id, sha_list)

        return B2File(self, response)

    async def _start_large_upload(self, file_name, mime_content_type):
        """ b2_start_large_file """
        # Start the request
        large_file_response = await self.connector.post(
            path=API.upload_large,
            params={
                'bucketId': self.id,
                'fileName': b2_url_encode(file_name),
                'contentType': mime_content_type or 'b2/x-auto'
            })
        return large_file_response.get('fileId', None)

    async def _upload_large_file_parts(self, file_id):
        """ b2_upload_part """
        async def upload_part_async(chunk, part_number):
            json = await self._upload(
                endpoint=API.uppload_url,
                handler=self.connector.upload_part,
                contents=chunk,
                part_number=part_number,
                content_length=content_length)
            return json.get('contentSha1', None)

        def file_io_thread(loop):
            futures = []
            iterator = _chunk_files(contents.name, content_length)
            for idx, chunk in enumerate(iterator):
                futures.append(asyncio.run_coroutine_threadsafe(
                    upload_part_async(chunk, idx),
                    loop))
            return [future.result() for future in futures]

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, file_io_thread, loop)

    async def _finish_large_file(self, file_id, sha_list):
        """ b2_finish_large_file """
        return await self.connector.post(
            path=API.upload_large_finish,
            params={
                'fileId': file_id,
                'partSha1Array': sha_list
            })

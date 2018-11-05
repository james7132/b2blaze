from aiob2.api import API
from aiob2.exceptions import B2Exception
from aiob2.utilities import b2_url_encode, b2_url_decode


class B2File():
    """

    """

    def __init__(self, bucket, json):
        """

        :param parent_list:
        :param json:
        """
        self.bucket  = bucket
        self.connector = parent.connector
        self.deleted = False

        self.id = json['fileId']
        # self.file_name_decoded = b2_url_decode(fileName)
        #TODO:  Find out if this is necessary
        self.name = json['fileName']
        self.content_sha1 = json['contentSha1']
        self.content_length = json['contentLength']
        self.content_type = json['contentType']
        self.file_info = json['fileInfo']
        self.action = json['action']
        self.uploadTimestamp = json['uploadTimestamp']

    async def get_versions(self, limit=None):
        """ Fetch list of all versions of the current file.
            Params:
                limit: (int) Limit number of results returned (optional, default 10000)

            Returns:
                file_versions (list) B2FileObject of all file versions
        """
        response = await self.connector.post(
            path=API.list_file_versions,
            params={
                'bucketId': self.bucket.id,
                'maxFileCount': limit or 10000,
                'startFileId': self.id,
                'startFileName': self.name,
            })

        return [B2File(self, file_json) for file_json in response['files']]

    async def hide(self):
        """Soft-delete a file (hide it from files list, but previous versions
        are saved.)

        b2_hide_file
        """
        await self.connector.post(
            path=API.delete_file,
            params={
                'bucketId': self.bucket.id,
                'fileName': b2_url_encode(self.name)
            })
        self.deleted = True
        # Delete from parent list if exists
        self.parent_list._files_by_name.pop(self.name)
        self.parent_list._files_by_id.pop(self.file_id)

    async def delete(self):
        """ Delete a file version (Does not delete entire file history: only a
        single version)

        b2_delete_file
        """
        await self.connector.post(
            path=API.delete_file_version,
            params={
                'fileId': self.file_id,
                'fileName': b2_url_encode(self.name)
            })
        self.deleted = True

    def download(self):
        """ Download latest file version """
        return self.connector.download_file(file_id=self.file_id)

    @property
    def download_url(self):
        """ Return file download URL """
        return self.connector.download_url + '?fileId=' + self.file_id

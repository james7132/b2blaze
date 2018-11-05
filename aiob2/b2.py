from aiob2.exceptions import B2ApplicationKeyNotSet, B2KeyIDNotSet
from aiob2.connector import B2Connector
import aiohttp
import os
import json


class B2():

    def __init__(self, loop=None):
        self.session = aiohttp.ClientSession(loop=loop)
        self.connector = B2Connector(self.session)

    def authenticate(self, key_id=None, application_key=None):
        """ b2_authorize_account """
        if key_id is None or application_key is None:
            key_id = os.environ.get('B2_KEY_ID', None)
            application_key = os.environ.get('B2_APPLICATION_KEY', None)
        if key_id is None:
            raise B2KeyIDNotSet
        if application_key is None:
            raise B2ApplicationKeyNotSet
        return self.connector._authorize(key_id=key_id,
                                         application_key=application_key)

    def list_buckets(self, types=None):
        """ Fetches a list of all buckets accessible by the client.
        Can be filtered on types using the `types` parameter.
        """
        return self._list_buckets(types=types)

    async def get_bucket(self, name=None, id=None):
        """ Gets a bucket by name or by ID. """
        async for bucket in self._list_buckets(id=id, name=None):
            assert bucket.id == id or bucket.name == name
            return bucket # Take the first bucket provided
        # TODO(james7132): Raise an error here?
        return None

    async def create_bucket(self, bucket_name, security, configuration=None):
        if type(bucket_name) != str and type(bucket_name) != bytes:
            raise B2InvalidBucketName("Bucket name must be alphanumeric or '-")
        if type(configuration) != dict and configuration is not None:
            raise B2InvalidBucketConfiguration
        response = await self.connector.post(
                path=API.create_bucket,
                account_id_required=True,
                params={
                    'bucketName': bucket_name,
                    'bucketType': security,
                    #TODO: bucketInfo
                    #TODO: corsRules
                    #TODO: lifeCycleRules
                })
        return B2Bucket(self, response)

    async def _list_buckets(self, id=None, name=None, types=None):
        """ b2_list_buckets """
        params = {}
        if id is not None:
            params['bucketId'] = id
        if name is not None:
            params['bucketName'] = name
        if types is not None:
            params['bucketTypes'] = json.dumps(list(types))

        response = await self.connector.put(
            path=API.list_all_buckets,
            account_id_required=True,
            params=params)

        for bucket_json in response['buckets']:
            yield B2Bucket(self, bucket_json)

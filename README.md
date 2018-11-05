# aiob2

aiob2 is a asyncio-based Backblaze B2 client for Python.

This library will allow you to easily interact with B2 buckets and files as first
class objects in Python 3.5+.

This is a hard-fork of [sibblegp/b2blaze](https://github.com/sibblegp/b2blaze).
changed to use aiohttp instead of requests.

## Installation

aiob2 requires Python 3.5.2+, and will  not work on any olderversion of Python.
To install aiob2, run the following command in the proper environment:

```bas aiobh
pip install aiob2
```

# Usage

## The B2 Object

```python
# Construct the B2 Client
from aiob2 import B2

# The client requires a aiohttp.ClientSession to operate under.
async with aiohttp.ClientSession() as session:
    b2_client = B2()

    # Authorize the client via enviorment vairables
    await b2_client.authorize()

    # Or explicitly authorize with keys.
    await b2_client.authorize(key_id, application_key)
```

The B2 object is how you access aiob2's functionality. You can optionally pass
in "key_id" and "application_key" as named arguments but you should probably set
them as environment variable as described above.

## Buckets

Buckets are essentially the highest level folders in B2, similar to how buckets
are used in AWS S3.

#### Bucket Properties

```python
bucket_id
bucket_name
bucket_type
bucket_info
lifecycle_rules
revision
cors_rules
deleted
```

#### List All Buckets

```python
async for bucket in b2.buckets.all():
    # iterate throug buckets
```

#### Create a Bucket

```python
bucket = await b2.buckets.create('test_bucket', security=b2.buckets.public)
```

Buckets can either be public or private. This does not change the functionality
of the library other than that you will need to manually authorize when using
file URLs (see below).

#### Retrieve a bucket

```python
bucket_by_name = await b2.buckets.get('test_bucket')
bucket_by_id = await b2.buckets.get(bucket_id='abcd')
```

#### Delete a bucket

```python
await bucket.delete()
```

## Files

Files are the same files you store locally. They can be stored inside folders
placed in buckets but this means they simply have a name like "folder/test.txt".
There is no distinction between folders and files.

#### File Properties

```python
file_id
file_name
content_sha1
content_length
content_type
file_info
action
uploadTimestamp
deleted
```

#### List All Files in a Bucket

NOTE: There may be tens of thousands of files (or more) in a bucket. This
operation will get information and create objects for all of them. It may take
quite some time and be computationally expensive to run.

```python
async for file in bucket.list_files():
    # iterate through all files in the bucket

async for file in bucket.list_files(limit=1000):
    # iterate through a limited number of files within the bucket
```

#### Upload a File

```python
text_file = open('hello.txt', 'rb')
new_file = await bucket.upload_file(contents=text_file,
                                    file_name='folder/hello.txt')
```

NOTE: You don't have to call `.read()` and instead can send the file directly to
contents. This will allow the file buffer directly over HTTP to B2 and save a
significant amount of memory. `contents` must be binary or a binary file.

#### Upload a Large File

```python
large_file = open('large_file.bin', 'rb')
new_file = await bucket.upload_large_file(contents=large_file,
                                          file_name='folder/large_file.bin')
```

NOTE: You cannot call `.read()` on the file because the function will seek and
buffer the file over for you. Per
[Backblaze recommendation](https://www.backblaze.com/b2/docs/large_files.html),
`part_size` defaults to `recommendedPartSize` from `b2_authorize_account`
(typically 100MB). The minimum part size is 5MB and you must have must have at
least 2 parts. This function uses the asyncio default
`concurrent.futures.ThreadPoolExecutor` to parallelize the upload.

#### Retrieve a File's Information (Necessary before Downloading)

```python
file_by_name = await bucket.get_file(name='folder/hello.txt')
file_by_id = await bucket.get_file(id='abcd1234')
```

#### Download a file

```python
file = await bucket.get_file(name='folder/hello.txt')
async with file.download() as response:
    chunk = await response.content.read(10)
```

NOTE: Unlike the rest of the library, this function returns the raw `aiohttp`
Response object for easier manipulation of the download, aiob2 simply
facilitates finding the correct download location for the request.

#### Getting all versions of a file

```python
file = await bucket.get_file(name='folder/hello.txt')
file_versions = await file.get_versions()
for file in file_versions:
    # work with multiple versions
```

The number of versions retrieved can be limited by passing in a `limit`
parameter. By default this value is set to the absolute maximum of 10,000.

```python
file_versions = await file.get_versions(limit=10)
for file in file_versions:
    # work with only 10 versions
```

#### Delete a file version

```python
await file.delete()
```

This deletes a single version of a file. (See the
[docs on File Versions](https://www.backblaze.com/b2/docs/b2_delete_file_version.html)
at Backblaze for explanation)

To completely delete all versions of a file, fetch all versions and call delete
on every version:

```python
file = await bucket.get_file(name='folder/hello.txt')
file_versions = await file.get_versions()

# This will simultaneously fire off as many delete requests as possible.
# You may be rate limited, depending on how many requests are made.
await asyncio.gather(*[version.delete() for version in file_versions])
```

#### Hide (aka "Soft-delete") a file

```python
await file.hide()
```

This hides a file (aka "soft-delete") so that downloading by name will not find
the file, but previous versions of the file are still stored. (See the
[docs on Hiding file](https://www.backblaze.com/b2/docs/b2_hide_file.html) at
Backblaze for details)

## Testing

** Running tests **

``` bash
python -m unittest discover
```

Before running, you must set the environment variables:
`B2_KEY_ID` and `B2_APPLICATION_KEY`

## LICENSE

MIT License

Copyright (c) 2018 James Liu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

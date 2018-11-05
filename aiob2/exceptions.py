import json


API_EXCEPTION_CODES = {
    400: B2RequestError,
    401: B2UnauthorizedError,
    403: B2ForbiddenError,
    404: B2FileNotFoundError,
    408: B2RequestTimeoutError,
    429: B2TooManyRequestsError,
    500: B2InternalError,
    503: B2ServiceUnavailableError,
}


class B2B2Exception(Exception):
    """ Base exception class for the Backblaze API """

    @staticmethod
    async def parse(response):
        """ Parse the response error code and return the related error type. """

        try:
            response_json = await response.json()
            status = int(response_json['status'])

            # Return B2B2Exception if unrecognized status code
            ErrorClass = API_EXCEPTION_CODES.get(status, B2B2Exception)
            return ErrorClass('{} - {}: {}'.format(status,
                                                   response_json['code'],
                                                   response_json['message']))
        except:
            return B2Exception('error parsing response. status code - {} '
                               'Response JSON: {}'.format(response.status,
                                                          response_json))


class B2ApplicationKeyNotSet(B2Exception):
    """ You must set the B2_KEY_ID environment variable before running the
    application
    """
    pass


class B2KeyIDNotSet(B2Exception):
    """ You must set the B2_APPLICATION_KEY environment variable before running
    the application
    """
    pass


class B2BucketDeleted(B2Exception):
    """ The bucket that is intended to be operated on has been deleted and
    cannot be used anymore.
    """
    pass


class B2FileNotFoundError(B2Exception):
    """ 404 Not Found """
    pass


class B2RequestError(B2Exception):
    """ There is a problem with a passed in request parameters. See returned message for details """
    pass


class B2UnauthorizedError(B2Exception):
    """ When calling b2_authorize_account, this means that there was something wrong with the accountId/applicationKeyId or with the applicationKey that was provided. The code unauthorized means that the application key is bad. The code unsupported means that the application key is only valid in a later version of the API.

    The code unauthorized means that the auth token is valid, but does not allow you to make this call with these parameters. When the code is either bad_auth_token or expired_auth_token you should call b2_authorize_account again to get a new auth token.
    """
    pass


class B2ForbiddenError(B2Exception):
    """ You have a reached a storage cap limit, or account access may be impacted in some other way; see the human-readable message.
    """
    pass


class B2RequestTimeoutError(B2Exception):
    """ The service timed out trying to read your request. """
    pass


class B2OutOfRangeError(B2Exception):
    """ The Range header in the request is outside the size of the file.. """
    pass


class B2TooManyRequestsError(B2Exception):
    """ B2 may limit API requests on a per-account basis. """
    pass


class B2InternalError(B2Exception):
    """ An unexpected error has occurred. """
    pass


class B2ServiceUnavailableError(B2Exception):
    """ The service is temporarily unavailable. The human-readable message
    identifies the nature of the issue, in general we recommend retrying with an
    exponential backoff between retries in response to this error.
    """
    pass


class B2InvalidBucketName(B2Exception):
    """ Bucket name must be alphanumeric or '-' """
    pass


class B2InvalidBucketConfiguration(B2Exception):
    """ Value error in bucket configuration """
    pass


class B2AuthorizationError(B2Exception):
    """ An error with the authorization request """
    pass


class B2InvalidRequestType(B2Exception):
    """ Request type must be get or post """
    pass

from prozorro.medicines.logging import request_id_var
from aiohttp.web import middleware
from uuid import uuid4
import logging


logger = logging.getLogger(__name__)


@middleware
async def request_id_middleware(request, handler):
    """
    Sets request_id contextvar and request['request_id']
    :param request:
    :param handler:
    :return:
    """
    value = request.headers.get('X-Request-ID', str(uuid4()))
    request_id_var.set(value)  # for loggers inside context
    response = await handler(request)
    response.headers['X-Request-ID'] = value  # for AccessLogger
    return response


@middleware
async def request_unpack_params(request, handler):
    """
    middleware for the func views
    to pass variables from url
    as kwargs
    """
    if 'swagger' in request.path:
        return await handler(request)
    return await handler(request, **request.match_info)

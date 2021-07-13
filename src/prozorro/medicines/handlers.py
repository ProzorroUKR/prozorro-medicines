import logging
from aiohttp.web import Response, HTTPNotFound
from aiohttp_swagger import swagger_path
from collections import OrderedDict
from prozorro import version as api_version
from prozorro.medicines import db
from prozorro.medicines.serialization import json_response
import json
logger = logging.getLogger(__name__)


@swagger_path('/swagger/ping.yaml')
async def ping_handler(request):
    return Response(text="pong")


@swagger_path('/swagger/version.yaml')
async def get_version(request):
    return json_response({'api_version': api_version})


@swagger_path('/swagger/registry.yaml')
async def get_registry(request, name):
    registry = await db.get_registry(name)
    if registry is None:
        raise HTTPNotFound(
            text=json.dumps({"error": f"{name}.json not found"}),
            content_type="application/json"
        )
    registry["data"] = OrderedDict(registry["data"])
    return json_response(registry)

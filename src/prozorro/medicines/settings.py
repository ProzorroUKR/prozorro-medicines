from pymongo import ReadPreference
from pymongo.write_concern import WriteConcern
from pymongo.read_concern import ReadConcern
from zoneinfo import ZoneInfo
import sys
import os

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://mongo:27017/")
ENGINE_DB_NAME = os.environ.get("ENGINE_DB_NAME", "medicines")
# 'PRIMARY', 'PRIMARY_PREFERRED', 'SECONDARY', 'SECONDARY_PREFERRED', 'NEAREST',
READ_PREFERENCE = getattr(ReadPreference, os.environ.get("READ_PREFERENCE", "PRIMARY"))
raw_write_concert = os.environ.get("WRITE_CONCERN", "1")
WRITE_CONCERN = WriteConcern(w=int(raw_write_concert) if raw_write_concert.isnumeric() else raw_write_concert)
READ_CONCERN = ReadConcern(level=os.environ.get("READ_CONCERN") or None)

SWAGGER_DOC_AVAILABLE = bool(os.environ.get("SWAGGER_DOC_AVAILABLE", True))

IS_TEST = "test" in sys.argv[0]
SENTRY_DSN = os.getenv('SENTRY_DSN')
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", 'Europe/Kiev'))

STALE_REGISTRIES_COUNT = int(os.environ.get("STALE_REGISTRIES_COUNT", 2))
REGISTRY_XML_URL = os.getenv('REGISTRY_XML_URL', "http://www.drlz.com.ua/reestr.xml")
REGISTRY_NAMES = os.getenv('REGISTRY_NAMES', "inn,atc,inn2atc,atc2inn").split(",")

XML_ENCODING = os.environ.get("XML_ENCODING", "windows-1251")
XML_SKIP_LINES = os.environ.get(
    "XML_SKIP_LINES",
    "<?xml version=\"1.0\" encoding=\"Windows-1251\"?>\r\n|<doc-list>\r\n".split("|")
)
XML_TAIL = os.environ.get("XML_TAIL", "</doc-list>\r\n")

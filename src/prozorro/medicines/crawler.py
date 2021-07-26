import asyncio
import aiohttp
import logging
from datetime import datetime
from xml.etree import ElementTree
from collections import defaultdict
from prozorro.medicines.db import insert_registry, init_mongodb, delete_stale_registries
from prozorro.medicines.logging import setup_logging
from prozorro.medicines.settings import (
    REGISTRY_XML_URL, XML_SKIP_LINES, XML_ENCODING, XML_TAIL,
    TIMEZONE, REGISTRY_NAMES,
)
from prozorro.medicines.utils import async_retry


logger = logging.getLogger(__name__)


class XMLChunkProcessor:
    """
    gets parts of an xml file,
    splits it
    """
    def __init__(self, split_by):
        self.tail = ""
        self.split_by = split_by

    def process_chunk(self, text):
        text = self.tail + text
        self.tail = ""

        parts = text.split(self.split_by)
        if parts:
            # checking incomplete tail
            self.tail = parts.pop()
            # yield parts
            for part in parts:
                yield part + self.split_by


class JSONRRegistries:
    def __init__(self):
        self.inn = {}
        self.atc = {}
        self.inn2atc = defaultdict(set)
        self.atc2inn = defaultdict(set)

    def update(self, node):
        mnn = node.find('mnn').text
        if mnn is not None:
            mnn = mnn.replace('*', '')
            self.inn[mnn.lower()] = mnn

        atc1 = node.find('atc1').text
        if atc1 is not None:
            atc1 = atc1.replace('*', '')
            self.atc[atc1] = atc1

            if mnn is not None:
                self.inn2atc[mnn.lower()].add(atc1)
                self.atc2inn[atc1].add(mnn.lower())

    async def save(self):
        for k, v in self.inn2atc.items():
            self.inn2atc[k] = tuple(v)

        for k, v in self.atc2inn.items():
            self.atc2inn[k] = tuple(v)

        now = datetime.now(TIMEZONE).replace(microsecond=0).isoformat()
        for name in REGISTRY_NAMES:
            if hasattr(self, name):
                await insert_registry({
                    "type": name,
                    "data": tuple(sorted(getattr(self, name).items(), key=lambda e: e[0])),
                    "dateModified": now,
                })
                logger.info(f"Updated {name} at {now}")
            else:
                logger.error(f"Unknown registry {name}")


@async_retry(tries=100, delay=1, backoff=2, max_delay=60)
async def import_registry():
    async with aiohttp.ClientSession() as session:
        async with session.get(REGISTRY_XML_URL, trust_env=True) as resp:
            if resp.status != 200:
                raise AssertionError(f"Unsuccessful response {resp.status} "
                                     f"{(await resp.text(encoding=XML_ENCODING))[:200]}")

            # skipping first lines
            for skip_line in XML_SKIP_LINES:
                line = await resp.content.readline()
                line = line.decode(encoding=XML_ENCODING)
                if line != skip_line:
                    logger.warning(f"Unexpected first line(check file format): {line}")

            # init parsing helpers
            registries = JSONRRegistries()
            xml_processor = XMLChunkProcessor(split_by="</doc>\r\n")
            # load data from <doc>..</doc> chunks
            count = 0
            async for data in resp.content.iter_chunked(1024 * 1024):
                text = data.decode(encoding=XML_ENCODING)
                for item in xml_processor.process_chunk(text):
                    xml = ElementTree.fromstring(item)
                    registries.update(xml)
                    count += 1
                    if count % 1000 == 0:
                        logger.info(f"Loaded {count} items from xml file")
            logger.info(f"Loaded {count} items from xml file")

            await registries.save()
            # the file end
            if xml_processor.tail != XML_TAIL:
                logger.warning(f"Unexpected tail(check file format): {xml_processor.tail}")


async def clean_up():
    for name in REGISTRY_NAMES:
        result = await delete_stale_registries(name)
        logger.info(f"Deleted {len(result)} old {name}.json registries")


def main():
    setup_logging()
    logger.info("Starting importing registry")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_mongodb())
    loop.run_until_complete(import_registry())
    loop.run_until_complete(clean_up())


if __name__ == "__main__":
    main()

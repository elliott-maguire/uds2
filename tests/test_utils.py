"""
tests.test_utils
~~~~~~~~~~~~~~~~~

This module implements the unit tests for the `utils` module.
"""

import os

from aperio.utils import build, rebuild
from aperio.models import AperioFile

from tests.utils import async_test, make_client, make_file, cleanup


class TestUtils:
    """ Test class for the `utils` module. """

    def test_build(self):
        new = open("temp", mode="w+")
        new.write("temp")
        new.close()

        file = build("temp")

        assert type(file) is AperioFile
        assert file.name == "temp"

        os.remove("temp")

    @async_test
    async def test_rebuild(self):
        client = make_client()
        file, r = await make_file(client)
        sheet, data = await client.get(r.get("spreadsheetId"))

        built = rebuild(sheet, data)

        assert type(built) is AperioFile
        assert built.name == "temp"

        await cleanup(client, r.get("spreadsheetId"))

#!/usr/bin/env python3.5

import argparse
import http.client
import json
import os
import os.path
import re
import shutil
import tempfile

BING_SERVER = "www.bing.com"

BING_URL_INDEX = (
    "/HPImageArchive.aspx?"
    "format=js&idx=%(index)s&n=%(num)s&mkt=%(country)s")

BING_PATTERN_IMAGE = (
    "^"
    "(.*)/"  # Directory
    "([a-zA-Z]+)"  # Name
    "_"
    "([A-Z][A-Z]-[A-Z][A-Z])"  # Country
    "([0-9]+)"  # Identifier
    "_"
    "([0-9]+x[0-9]+)"  # Resolution
    "\."
    "(.*)"  # Extension
    "$"
)

LOCAL_IMAGE_NAME = "%(name)s_%(identifier)s_%(resolution)s.%(extension)s"


class BingWallpaperDownloader(object):

    def __init__(self, directory, countries, resolution):

        if type(countries) == str:
            self.countries = [countries]
        else:
            self.countries = countries

        self.resolution = resolution

        self.dir_tmp = tempfile.mkdtemp(prefix="bing_")

        self.dir_storage = directory

        if not os.path.exists(self.dir_storage):
            os.makedirs(self.dir_storage)

    def __del__(self):

        shutil.rmtree(self.dir_tmp)

    def retrieve_index(self, country):
        """Retrieve image index for the specified country"""

        args = {
            "index": 0,
            "num": 8,
            "country": country
        }

        self.client = http.client.HTTPConnection(BING_SERVER)
        self.client.request("GET", BING_URL_INDEX % args)

        response = self.client.getresponse()
        if response.status == http.client.OK:

            path_index = os.path.join(self.dir_tmp, "index.json")
            fp = open(path_index, "wb")
            fp.write(response.read())
            fp.close()

            fp = open(path_index, "r")
            return json.loads(fp.read())

        else:
            return None

    def parse_index(self, data):
        """Read image index and return URLs"""

        images = data.get("images")
        if images is None:
            return None

        for image in images:
            url = image.get("url")
            if url is None:
                continue

            yield url

    @staticmethod
    def parse_url(url):

        match = re.match(BING_PATTERN_IMAGE, url)
        if match is None:
            return None

        return {
            "directory": match.group(1),
            "name": match.group(2),
            "country": match.group(3),
            "identifier": match.group(4),
            "resolution": match.group(5),
            "extension": match.group(6)
        }

    def retrieve_image(self, url, path_image):

        print(url)
        self.client.request("GET", url)
        response = self.client.getresponse()

        fd = open(path_image, "wb")
        fd.write(response.read())
        fd.close()

    def run(self):

        for country in self.countries:

            data_index = self.retrieve_index(country)

            for url in self.parse_index(data_index):

                data_image = self.parse_url(url)
                url = url.replace(data_image["resolution"], self.resolution)

                data_image["resolution"] = self.resolution
                filename = LOCAL_IMAGE_NAME % data_image

                path_image = os.path.join(self.dir_storage, filename)

                if os.path.exists(path_image):
                    print("%s: already downloaded" % filename)
                    continue

                self.retrieve_image(url, path_image)
                print(path_image)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--country", default="fr-FR", help="Country to download")
    parser.add_argument(
        "--resolution", default="1920x1200", help="Country to download")
    parser.add_argument(
        "--storage", default="./bing", help="Storage directory")

    args = parser.parse_args()

    downloader = BingWallpaperDownloader(
        args.storage, args.country, args.resolution)
    downloader.run()

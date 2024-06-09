#!/usr/bin/python3

import json
import os
from pathlib import Path
from typing import Dict, List
import requests


# TODO: update key
class UploadToStrava:

    # path to source directory
    srcDir = f"{os.path.expanduser('~')}/.openambit"
    # path to destination directory
    destDir = f"{os.path.dirname(os.path.realpath(__file__))}/data"

    def __init__(self, data_dir: Path, assets_dir: Path):
        self.data_dir = data_dir
        self.assets_dir = assets_dir

    def upload(self, file_list: List):
        keys = {}
        keyFile = self.assets_dir.joinpath("key.json")

        if not Path.exists(keyFile):
            assert "Create key file"

        with open(keyFile) as f:
            keys = json.load(f)
            print(keys)

        # Check if token is valid
        responseMap = self._getAthleteData(keys["access_token"])

        if "message" in responseMap and responseMap["message"] == "Authorization Error":
            if (
                "errors" in responseMap
                and responseMap["errors"][0]["field"] == "access_token"
            ):
                updatedKey = self._updateToken(keys["refresh_token"])
                with open(keyFile, "w") as f:
                    json.dump(updatedKey, f)

        # Upload file
        for upload_file in file_list:
            response = self._postFile(upload_file, keys["access_token"])
            if (200 <= response.status_code and 300 > response.status_code):
                print(f"File {upload_file} successfully uploaded")
            else:
                print(f"Issue uploading file {upload_file}, status code: {response.status_code}")

    def _postFile(self, file: str, token: str):
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            'data_type': 'gpx'
        }
        files = {
            'file': open(file, 'rb')
        }

        response = requests.post(
            url="https://www.strava.com/api/v3/uploads",
            headers=headers,
             params=params,
             files=files,
        )
        # print(response.request.url)
        # print(response.request.body)
        # print(response.raw)
        # print(response.text)
        return response

    def _getAthleteData(self, token: str) -> Dict:
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(
            f"https://www.strava.com/api/v3//athlete", headers=headers
        )
        print(response.request.url)
        print(response.request.body)
        print(response.raw)
        print(response.text)
        return json.loads(response.text)

    def _updateToken(self, refreshToken: str):
        response = requests.post(
            f"https://www.strava.com/oauth/token",
            data={
                "client_id": "116610",
                "client_secret": "f44b74815bb515e8cb21f014339f6e7459316bf4",
                "grant_type": "refresh_token",
                "refresh_token": refreshToken,
            },
        )
        print(response.request.url)
        print(response.request.body)
        print(response.raw)
        print(response.text)
        return json.loads(response.text)

    # curl -X POST https://www.strava.com/oauth/token \
    #   -d client_id=116610 \
    #   -d client_secret=f44b74815bb515e8cb21f014339f6e7459316bf4 \
    #   -d grant_type=refresh_token \
    #   -d refresh_token=20698b5a4a1aee31d8fd4ab5b9dc90b9e9c038e6

    def _getSport(self, rootIn):
        for element in rootIn.iterfind("Log/Header/ActivityTypeName"):
            print(element.text)
            return element.text

# Copyright 2019, 2020 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module that defines a Downloader object to get HTTP urls."""

import re
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

import requests


from ccx_data_pipeline.data_pipeline_error import DataPipelineError


# pylint: disable=too-few-public-methods
class HTTPDownloader:
    """Downloader for HTTP uris."""

    # https://<hostname>/service_id/file_id?<credentials and other params>
    HTTP_RE = re.compile(
        r"^(?:https://[^/]+\.s3\.amazonaws\.com/[0-9a-zA-Z/\-]+|"
        r"http://minio:9000/insights-upload-perma/[0-9a-zA-Z\.\-]+/[0-9a-zA-Z\-]+)\?"
        r"X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=[^/]+$"
    )

    # pylint: disable=no-self-use
    @contextmanager
    def get(self, src):
        """Download a file from HTTP server and store it in a temporary file."""
        if src is None or not HTTPDownloader.HTTP_RE.fullmatch(src):
            raise DataPipelineError(f"Invalid URL format: {src}")

        try:
            response = requests.get(src)
            data = response.content

            if len(data) == 0:
                raise DataPipelineError(f"Empty input archive from {src}")

            with NamedTemporaryFile() as file_data:
                file_data.write(data)
                file_data.flush()
                yield file_data.name

            response.close()

        except requests.exceptions.ConnectionError as err:
            raise DataPipelineError(err)
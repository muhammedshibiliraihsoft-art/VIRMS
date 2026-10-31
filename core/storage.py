"""Private S3-compatible storage boundary; endpoint configuration selects R2."""

import os

import boto3

from django.core.files.base import File
from django.core.files.storage import Storage


class PrivateObjectStorage(Storage):
    def __init__(self):
        self.bucket = os.environ["OBJECT_STORAGE_BUCKET"]
        self.client = boto3.client(
            "s3",
            endpoint_url=os.environ["OBJECT_STORAGE_ENDPOINT"],
            aws_access_key_id=os.environ["OBJECT_STORAGE_ACCESS_KEY"],
            aws_secret_access_key=os.environ["OBJECT_STORAGE_SECRET_KEY"],
            region_name=os.getenv("OBJECT_STORAGE_REGION", "auto"),
        )

    def _open(self, name, mode="rb"):
        if mode != "rb":
            raise ValueError("Object storage supports binary reads only")
        response = self.client.get_object(Bucket=self.bucket, Key=name)
        return File(response["Body"], name=name)

    def _save(self, name, content):
        self.client.upload_fileobj(content, self.bucket, name)
        return name

    def delete(self, name):
        self.client.delete_object(Bucket=self.bucket, Key=name)

    def exists(self, name):
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except ClientError as error:
            if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise

    def size(self, name):
        response = self.client.head_object(Bucket=self.bucket, Key=name)
        return response["ContentLength"]

    def url(self, name):
        raise NotImplementedError("Private objects require an authorized delivery flow")

import boto3
import requests
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from django.conf import settings


class S3:
    GET = 'get_object'
    PUT = 'put_object'

    @staticmethod
    def _conn():
        session = S3._session()

        return session.client(
            's3',
            config=Config(signature_version='s3v4')
        )

    @staticmethod
    def _session():
        return boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    @classmethod
    def generate_signed_url(cls, accessor, key):
        try:
            _conn = cls._conn()
            return _conn.generate_presigned_url(
                accessor,
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=600,
            )
        except NoCredentialsError:  # pragma: no cover
            pass

    @classmethod
    def upload(cls, file_path, file_content, headers=None):
        url = cls.generate_signed_url(cls.PUT, file_path)
        result = None
        if url:
            res = requests.put(
                url, data=file_content, headers=headers
            ) if headers else requests.put(url, data=file_content)
            result = res.status_code

        return result

    @classmethod
    def upload_file(cls, file_path, headers=None):
        return cls.upload(file_path, open(file_path, 'r').read(), headers)

    @classmethod
    def upload_public(cls, file_path, file_content):
        try:
            client = cls._conn()
            return client.upload_fileobj(
                file_content,
                settings.AWS_STORAGE_BUCKET_NAME,
                file_path,
                ExtraArgs={'ACL': 'public-read'},
            )
        except NoCredentialsError:  # pragma: no cover
            pass

    @classmethod
    def url_for(cls, file_path):
        return cls.generate_signed_url(cls.GET, file_path) if file_path else None

    @classmethod
    def public_url_for(cls, file_path):
        return "http://{0}.s3.amazonaws.com/{1}".format(
            settings.AWS_STORAGE_BUCKET_NAME,
            file_path,
        )

    @classmethod
    def __fetch_keys(cls, prefix='/', delimiter='/'):  # pragma: no cover
        prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
        bucket = cls._session().resource('s3').Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        return [_.key for _ in bucket.objects.filter(Prefix=prefix)]

    @classmethod
    def missing_objects(cls, objects, prefix_path, sub_paths):  # pragma: no cover
        missing_objects = []

        if not objects:
            return missing_objects

        s3_keys = cls.__fetch_keys(prefix=prefix_path)

        if not s3_keys:
            return objects

        for obj in objects:
            paths = [obj.pdf_path(path) for path in sub_paths]
            if not all([path in s3_keys for path in paths]):
                missing_objects.append(obj)

        return missing_objects

    @classmethod
    def remove(cls, key):
        try:
            _conn = cls._conn()
            return _conn.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=key
            )
        except NoCredentialsError: # pragma: no cover
            pass
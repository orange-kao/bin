#!/usr/bin/python3

from datetime import datetime
from datetime import timedelta

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

class LazyS3:
    def __init__(self, bucket, storage_class='STANDARD', sse=None):
        self.s3_client = boto3.client('s3')
        self.bucket = bucket

        self.upload_transfer_config = TransferConfig(
                max_concurrency=1
        )
        self.upload_extra_args = {
                'StorageClass':storage_class, # 'STANDARD' or 'DEEP_ARCHIVE'
                'ServerSideEncryption':sse,
        }

        if self.upload_extra_args['ServerSideEncryption'] is None:
            del self.upload_extra_args['ServerSideEncryption']

    def get_obj_info_graceful(self, obj_name):
        obj_info = None
        try:
            obj_info = self.s3_client.head_object(
                    Bucket=self.bucket,
                    Key=obj_name,
            )
            del obj_info['ResponseMetadata']
            obj_info['ETag'] = obj_info['ETag'].strip('"')
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                pass
            else:
                raise

        return obj_info

    def put_obj(self, file_name, obj_name=None):
        if obj_name is None:
            obj_name = file_name

        self.s3_client.upload_file(
                Filename=file_name,
                Bucket=self.bucket,
                Key=obj_name,
                ExtraArgs=self.upload_extra_args,
                Config=self.upload_transfer_config,
        )

    def put_legal_hold(self, obj_name):
        self.s3_client.put_object_legal_hold(
                Bucket=self.bucket,
                Key=obj_name,
                LegalHold={
                    'Status':'ON'
                },
        )

    def put_gov_retention(self, obj_name, ret_days):
        self.s3_client.put_object_retention(
                Bucket=self.bucket,
                Key=obj_name,
                Retention={
                    'Mode':'GOVERNANCE',
                    'RetainUntilDate':datetime.now() + timedelta(days=ret_days)
                },
        )


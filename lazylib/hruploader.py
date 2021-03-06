#!/usr/bin/python3

import hashlib
import os

from lazylib.lazys3 import LazyS3
from lazylib.ddbobjlst import DyanomoDbObjectList

class HashedRetentionUploader:
    def __init__(self, bucket, storage_class, sse, dyna_table, dyna_region):
        self.lazy_s3 = LazyS3( bucket=bucket,
                                      storage_class=storage_class,
                                      sse=sse                      )

        self.dyna_list = DyanomoDbObjectList(dyna_table, dyna_region)

    @staticmethod
    def generate_file_hexdigest_dict(file_name):
        file_size = os.path.getsize(file_name)
        sha512 = hashlib.sha512()
        md5 = hashlib.md5()
        sha1_4k = hashlib.sha1()
        sha1_1m = hashlib.sha1()
        block_count = 0
        with open(file_name, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096),b''):
                sha512.update(byte_block)
                md5.update(byte_block)
                if block_count < 1:
                    sha1_4k.update(byte_block)
                if block_count < 256:
                    sha1_1m.update(byte_block)
                block_count += 1
        return {
            "size": file_size,
            "sha512": sha512.hexdigest(),
            "md5": md5.hexdigest(),
            "sha1_4k": sha1_4k.hexdigest(),
            "sha1_1m": sha1_1m.hexdigest(),
        }

    def upload(self, file_name):
        print(f"{repr(file_name)}")
        print(f"    -> ", end="", flush=True)
        file_hash_dict = self.generate_file_hexdigest_dict(file_name)
        obj_name = file_hash_dict["sha512"]
        exp_etag = file_hash_dict["md5"]
        print(f"{repr(obj_name)}")

        file_size = os.path.getsize(file_name)
        file_info = {
            "size": file_size,
            "md5": exp_etag,
            "sha1_4k": file_hash_dict["sha1_4k"],
            "sha1_1m": file_hash_dict["sha1_1m"],
        }

        # Check if it's listed in DynamoDB
        is_exist_dyna = self.dyna_list.is_object_exist(obj_name, file_info)
        if is_exist_dyna is True:
            # Already in DyanomoDB, do nothing
            print("    Already in DynamoDB.")
            return obj_name

        # Check if it's already in S3
        obj_info = self.lazy_s3.get_obj_info_graceful(obj_name)
        if obj_info is not None:
            # Not in DynamoDB, but already in S3
            # -> Validate object, put legal hold, add to DynamoDB

            if exp_etag != obj_info['ETag']:
                raise RuntimeError(
                        f"S3 ETag mismatch for file {repr(file_name)}, "
                        f"object {repr(obj_name)}, "
                        f"expected ETag {repr(exp_etag)}, "
                        f"actual ETag {repr(obj_info['ETag'])}, "
                        f"object info {repr(obj_info)}")

            print("    Already in S3.")

            if obj_info.get('ObjectLockLegalHoldStatus') != "ON":
                self.lazy_s3.put_legal_hold(obj_name)
                print("    Legal hold set.")

            self.dyna_list.add_object(obj_name, file_info)
            print("    DynamoDB updated.")
            return obj_name

        # Not in DyanomoDB, not in S3
        print("    Uploading to S3...")
        self.lazy_s3.put_obj(file_name, obj_name)
        print("    S3 upload completed.")
        self.lazy_s3.put_legal_hold(obj_name)
        print("    Legal hold set.")
        self.dyna_list.add_object(obj_name, file_info)
        print("    DynamoDB updated.")
        return obj_name


#!/usr/bin/env python3

import os
import hashlib
import shutil

class HashedCopyer:
    def __init__(self, dst_dir_list):
        self.dst_dir_list = dst_dir_list

    @staticmethod
    def generate_file_sha512(file_name):
        sha512 = hashlib.sha512()
        with open(file_name, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096),b''):
                sha512.update(byte_block)
        return sha512.hexdigest()

    def is_exist_at_any_dst(self, sha512):
        for dir_cand in self.dst_dir_list:
            if os.path.isfile(os.path.join(dir_cand, sha512)) is True:
                return True
        return False

    def get_writable_dst_dir(self):
        dst_dir = None
        for dir_cand in self.dst_dir_list:
            stat = os.statvfs(dir_cand)
            if ((1.0 - (stat.f_bavail / stat.f_blocks)) * 100) < 95.0:
                dst_dir = dir_cand
                break

        if dst_dir is None:
            raise RuntimeError("All destinations are 95%+ full")

        return dst_dir

    def copy(self, src_file, threshold_ts=None):
        if threshold_ts is not None:
            if os.path.getmtime(src_file) < threshold_ts:
#                print(f"{repr(src_file)}")
#                print("    File not modified, skip.")
                return

        print(f"{repr(src_file)}")
        print(f"    -> ", end="", flush=True)
        sha512 = self.generate_file_sha512(src_file)
        print(f"{repr(sha512)}")


        if self.is_exist_at_any_dst(sha512) is True:
            print("    Already exist, do nothing.")
            return

        dst_dir = self.get_writable_dst_dir()

        dst_file = os.path.join(dst_dir, sha512)
        dst_temp_file = os.path.join(dst_dir, "temp-file")

        shutil.copyfile(src_file, dst_temp_file)
        os.rename(dst_temp_file, dst_file)
        print("    Not exist, copied.")

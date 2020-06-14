#!/usr/bin/env python3

import os
import hashlib
import shutil
import socket
import re
import sys

class HashedCopyer:
    def __init__(self, dst_dir_list):
        self.dst_dir_list = dst_dir_list

    @staticmethod
    def is_valid_sha512(sha512_hex):
        pattern = re.compile("\A[0-9a-f]{128}\Z")
        if pattern.match(sha512_hex):
            return True
        return False

    @staticmethod
    def generate_file_sha512(file_pathname):
        sha512 = hashlib.sha512()
        with open(file_pathname, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096),b''):
                sha512.update(byte_block)
        return sha512.hexdigest()

    def find_exist_dst(self, dst_basename):
        for dir_cand in self.dst_dir_list:
            if os.path.isfile(os.path.join(dir_cand, dst_basename)) is True:
                return dir_cand
        return None

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

    def __copy(self, src_pathname, dst_basename, *, del_src=False):
        src_basename = os.path.basename(src_pathname)
        dst_dir = self.find_exist_dst(dst_basename)
        if dst_dir is not None:
            print(f"    Already exist in {dst_dir}")
            if del_src:
                os.remove(src_pathname)
                print(f"    Source deleted")
            return

        dst_dir = self.get_writable_dst_dir()
        dst_pathname = os.path.join(dst_dir, dst_basename)
        dst_temp_basename = "temp_{}_{}".format(socket.gethostname(), os.getpid())
        dst_temp_pathname = os.path.join(dst_dir, dst_temp_basename)

        try:
            if del_src and os.stat(src_pathname).st_dev == os.stat(dst_dir).st_dev:
                os.rename(src_pathname, dst_pathname)
                print(f"    Moved (rename) to {dst_dir}")
            elif del_src:
                shutil.copyfile(src_pathname, dst_temp_pathname)
                os.rename(dst_temp_pathname, dst_pathname)
                os.remove(src_pathname)
                print(f"    Moved (copy and delete) to {dst_dir}")
            else:
                shutil.copyfile(src_pathname, dst_temp_pathname)
                os.rename(dst_temp_pathname, dst_pathname)
                print(f"    Copied to {dst_dir}")
        except KeyboardInterrupt as e:
            print("Clearning up partial copy...")
            if os.path.isfile(dst_temp_pathname):
                os.remove(dst_temp_pathname)
            raise e

    def copy(self, src_pathname):
        print(repr(src_pathname))
        print(f"    -> ", end="", flush=True)
        sha512 = self.generate_file_sha512(src_pathname)
        print(repr(sha512))

        self.__copy(src_pathname, sha512, del_src=False)

    def move_src_repo(self, src_pathname):
        print(repr(src_pathname))
        src_basename = os.path.basename(src_pathname)

        if self.is_valid_sha512(src_basename) is not True:
            print("    ERROR: File name is not SHA512")
            sys.exit(1)

        self.__copy(src_pathname, src_basename, del_src=True)


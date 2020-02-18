#!/usr/bin/env python3

import tempfile
import os
from lazylib.locobjlst import LocalObjectList

def test_high_level_api():
    object_list = LocalObjectList(":memory:")

    with tempfile.TemporaryDirectory() as temp_dir:
        print(temp_dir)
        for basename in ["f1", "f2", "f3"]:
            pathname = os.path.join(temp_dir, basename)
            print(pathname)
            with open(pathname, "w") as f:
                f.write(basename)

        #with object_list.transaction() as t:
        object_list.add_repo_object_by_dir(1, temp_dir)

    for row in object_list.list_repo_object_by_revision(1):
        print(row)


def test_all():
    object_list = LocalObjectList(":memory:")

    object_info = {
        "size": 50,
        "md5": "MD5",
        "sha1_4k": "4K",
        "sha1_1m": "1M",
        "cloud_archive_status": "S3Std",
    }
    object_list.add_storage_object("objname", object_info)
    assert object_info.get("object_name") is None
    assert object_info.get("item_format") is None

    # Test get_storage_object() non-exist entry
    object_info = object_list.get_storage_object("obj_not_exist")
    assert object_info is None

    # Test get_storage_object()
    object_info = object_list.get_storage_object("objname")
    assert object_info["size"] == 50
    assert object_info["cloud_archive_status"] == "S3Std"

    # Test __update_storage_object()
#    object_info = {
#        "size": 100,
#        "cloud_archive_status": "GDA",
#    }
#    object_list.__update_storage_object("objname", object_info)

    # Test __update_storage_object() non-exist entry
#    object_info = {"sha1_4k": "400K"}
#    try:
#        object_list.__update_storage_object("obj_not_exist", object_info)
#    except RuntimeError as e:
#        assert isinstance(e, RuntimeError)
#    else:
#        assert False

    # Test __update_storage_object() and get_storage_object()
#    object_info = object_list.get_storage_object("objname")
#    assert object_info["size"] == 100
#    assert object_info["sha1_4k"] == "4K"
#    assert object_info["cloud_archive_status"] == "GDA"

    # Test update_storage_object_cloud_archive_status() and get_storage_object()
    object_list.update_cloud_archive_status("objname", "IA")
    object_info = object_list.get_storage_object("objname")
    assert object_info["cloud_archive_status"] == "IA"

    object_list.close()

def main():
    test_all()
    test_high_level_api()

if __name__ == "__main__":
    main()

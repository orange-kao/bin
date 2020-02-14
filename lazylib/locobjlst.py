#!/usr/bin/env python3

import sqlite3
from lazylib.hruploader import HashedRetentionUploader

class LocalObjectList:
    STORAGE_OBJECT_CURRENT_ITEM_FORMAT = 2
    STORAGE_OBJECT_COLUMNS = [
        "object_name",
        "size",
        "md5",
        "sha1_4k",
        "sha1_1m",
        "cloud_archive_status",
        "item_format",
    ]
    STORAGE_OBJECT_COLUMNS_EXC_PKEY = STORAGE_OBJECT_COLUMNS[1:]

    def __init__(self, db_filename):
        self.con = sqlite3.connect(db_filename)
        self.con.row_factory = self.__dict_factory
        self.con.execute("PRAGMA foreign_keys = ON;");
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS storage_objects (
                object_name TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                md5 TEXT NOT NULL,
                sha1_4k TEXT NOT NULL,
                sha1_1m TEXT NOT NULL,
                cloud_archive_status TEXT,
                item_format INTEGER
            );
        """)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS repo_objects (
                repo_revision INTEGER,
                repo_pathname TEXT NOT NULL,
                object_name TEXT NOT NULL,
                PRIMARY KEY (repo_revision, repo_pathname),
                FOREIGN KEY (object_name) REFERENCES storage_objects(object_name)
            );
        """)
        self.con.commit()

    def transactino(self):
        self.con.execute("BEGIN TRANSACTION;")
        yield
        self.con.execute("COMMIT;")
        self.con.commit()

    def add_storage_object_by_file(self, file_pathname):
        object_metadata = HashedRetentionUploader.generate_file_hexdigest_dict(file_pathname)
        object_metadata["cloud_archive_status"] = None
        self.add_storage_object(object_metadata["sha512"], object_metadata)

#    def add_storage_object_by_dir(self, dir_pathname):

    def add_storage_object(self, object_name, object_metadata):
        sql = "INSERT INTO storage_objects " \
              "       ( object_name,  size,  md5,  sha1_4k,  sha1_1m,  cloud_archive_status,  item_format) " \
              "VALUES (:object_name, :size, :md5, :sha1_4k, :sha1_1m, :cloud_archive_status, :item_format);"
        object_metadata_extra = {"object_name": object_name, "item_format": self.STORAGE_OBJECT_CURRENT_ITEM_FORMAT}
        self.con.execute(sql, {**object_metadata, **object_metadata_extra})

    def add_repo_object(self, repo_revision, repo_pathname, object_name):
        sql = "INSERT INTO repo_objects " \
              "       ( repo_revision,  repo_pathname,  object_name) " \
              "VALUES (:repo_revision, :repo_pathname, :object_name);"
        sql_dict = {
            "repo_revision": repo_revision,
            "repo_pathname": repo_pathname,
            "object_name": object_name,
        }
        self.con.execute(sql, sql_dict)

    @staticmethod
    def __dict_factory(cursor, row):
        row_dict = {}
        for idx, col in enumerate(cursor.description):
            row_dict[col[0]] = row[idx]
        return row_dict

    def get_storage_object(self, object_name):
        sql = "SELECT * FROM storage_objects WHERE object_name = ?;"
        row = self.con.execute(sql, (object_name, )).fetchone()
        return row

    def __update_dict_to_set_and_tuple(self, *, table_columns, update_dict, where_list):
        sql_list = []
        update_list = []
        for key in table_columns:
            if key in update_dict:
                sql_list.append(f"{key} = ?")
                update_list.append(update_dict[key])

        ret_sql = ", ".join(sql_list)
        ret_tuple = tuple(update_list + where_list)
        return ret_sql, ret_tuple

    def update_storage_object(self, object_name, dic):
        set_sql, sql_tuple = self.__update_dict_to_set_and_tuple(
            table_columns=self.STORAGE_OBJECT_COLUMNS_EXC_PKEY,
            update_dict=dic,
            where_list=[object_name],
        )
        sql = f"UPDATE storage_objects SET {set_sql} WHERE object_name = ?;"
        rowcount = self.con.execute(sql, sql_tuple).rowcount
        self.con.commit()
        if rowcount != 1:
            raise RuntimeError(f"Object {object_name} does not exist")

    def update_cloud_archive_status(self, object_name, cloud_archive_status):
        sql = f"UPDATE storage_objects SET cloud_archive_status = ? WHERE object_name = ?;"
        rowcount = self.con.execute(sql, (cloud_archive_status, object_name)).rowcount
        self.con.commit()
        if rowcount != 1:
            raise RuntimeError(f"Object {object_name} does not exist")

    def close(self):
        self.con.commit()
        self.con.close()

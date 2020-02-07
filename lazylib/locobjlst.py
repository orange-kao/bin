#!/usr/bin/env python3

import sqlite3

class LocalObjectList:
    CURRENT_ITEM_FORMAT = 2
    TABLE_COLUMNS = [
        "object_name",
        "size",
        "md5",
        "sha1_4k",
        "sha1_1m",
        "cloud_archive_status",
        "item_format",
    ]
    TABLE_COLUMNS_EXC_PKEY = TABLE_COLUMNS[1:]

    def __init__(self, db_filename):
        self.con = sqlite3.connect(db_filename)
        self.con.row_factory = self.__dict_factory
        self.con.execute("PRAGMA foreign_keys = ON;");
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS object_list (
                object_name TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                md5 TEXT NOT NULL,
                sha1_4k TEXT NOT NULL,
                sha1_1m TEXT NOT NULL,
                cloud_archive_status TEXT,
                item_format INTEGER
            );
        """)
        self.con.commit()

    def add(self, object_name, object_metadata):
        sql = "INSERT INTO object_list " \
              "       ( object_name,  size,  md5,  sha1_4k,  sha1_1m,  cloud_archive_status,  item_format) " \
              "VALUES (:object_name, :size, :md5, :sha1_4k, :sha1_1m, :cloud_archive_status, :item_format);"
        object_metadata_extra = {"object_name": object_name, "item_format": self.CURRENT_ITEM_FORMAT}
        self.con.execute(sql, {**object_metadata, **object_metadata_extra})
        self.con.commit()

    @staticmethod
    def __dict_factory(cursor, row):
        row_dict = {}
        for idx, col in enumerate(cursor.description):
            row_dict[col[0]] = row[idx]
        return row_dict

    def get(self, object_name):
        sql = "SELECT * FROM object_list WHERE object_name = ?;"
        row = self.con.execute(sql, (object_name, )).fetchone()
        return row

    def __update_dict_to_set_and_tuple(self, update_dic, where_list):
        sql_list = []
        update_list = []
        for key in self.TABLE_COLUMNS_EXC_PKEY:
            if key in update_dic:
                sql_list.append(f"{key} = ?")
                update_list.append(update_dic[key])

        ret_sql = ", ".join(sql_list)
        ret_tuple = tuple(update_list + where_list)
        return ret_sql, ret_tuple

    def update(self, object_name, dic):
        set_sql, sql_tuple = self.__update_dict_to_set_and_tuple(dic, [object_name])
        sql = f"UPDATE object_list SET {set_sql} WHERE object_name = ?;"
        rowcount = self.con.execute(sql, sql_tuple).rowcount
        self.con.commit()
        if rowcount != 1:
            raise RuntimeError(f"Object {object_name} does not exist")

    def update_cloud_archive_status(self, object_name, cloud_archive_status):
        sql = f"UPDATE object_list SET cloud_archive_status = ? WHERE object_name = ?;"
        rowcount = self.con.execute(sql, (cloud_archive_status, object_name)).rowcount
        self.con.commit()
        if rowcount != 1:
            raise RuntimeError(f"Object {object_name} does not exist")

    def close(self):
        self.con.commit()
        self.con.close()

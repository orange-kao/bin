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
    TABLE_COLUMNS_STR = ", ".join(TABLE_COLUMNS)
    TABLE_VALUES_STR = ", ".join(["?"] * len(TABLE_COLUMNS))
    TABLE_COLUMNS_EXC_PKEY = TABLE_COLUMNS[1:]

    def __init__(self, db_filename):
        self.con = sqlite3.connect(db_filename)

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

    def add(self, object_name, dic):
        sql = f"INSERT INTO object_list "
        sql += f"({self.TABLE_COLUMNS_STR}) VALUES ({self.TABLE_VALUES_STR});"

        self.con.execute(sql, (
            object_name,
            dic["size"],  # new in format 1
            dic["md5"],  # new in format 1
            dic["sha1_4k"],  # new in format 2
            dic["sha1_1m"],  # new in format 2
            dic.get("cloud_archive_status"),
            self.CURRENT_ITEM_FORMAT,
        ))
        self.con.commit()

    def __row_tuple_to_dict(self, row):
        dic = {}
        for index, data in enumerate(row):
            dic[self.TABLE_COLUMNS[index]] = data
        return dic

    def get(self, object_name):
        sql = f"SELECT {self.TABLE_COLUMNS_STR} "
        sql += f"FROM object_list WHERE object_name = ?;"
        for row in self.con.execute(sql, (object_name, )):
            dic = self.__row_tuple_to_dict(row)
            return dic
        return None

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
        s, t = self.__update_dict_to_set_and_tuple(dic, [object_name])
        sql = f"UPDATE object_list SET {s} WHERE object_name = ?;"
        rowcount = self.con.execute(sql, t).rowcount
        self.con.commit()
        return True if rowcount == 1 else False

    def close(self):
        self.con.commit()
        self.con.close()

    @staticmethod
    def main():
        l = LocalObjectList(":memory:")

        dic = {}
        dic["size"] = 50
        dic["md5"] = "MD5"
        dic["sha1_4k"] = "4K"
        dic["sha1_1m"] = "1M"
        dic["cloud_archive_status"] = "S3Std"
        l.add("objname", dic)

        # Test get() non-exist entry
        dic = l.get("obj_not_exist")
        assert(dic is None)

        # Test get()
        dic = l.get("objname")
        assert(dic["size"] == 50)
        assert(dic["cloud_archive_status"] == "S3Std")

        # Test update()
        dic = {}
        dic["size"] = 100
        dic["cloud_archive_status"] = "GDA"
        r = l.update("objname", dic)
        assert(r is True)

        # Test update() non-exist entry
        dic = {}
        dic["sha1_4k"] = "400K"
        r = l.update("obj_not_exist", dic)
        assert(r is False)

        # Test update() and get()
        dic = l.get("objname")
        assert(dic["size"] == 100)
        assert(dic["sha1_4k"] == "4K")
        assert(dic["cloud_archive_status"] == "GDA")

        l.close()

if __name__ == "__main__":
    LocalObjectList.main()


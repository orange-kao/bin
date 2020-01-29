#!/usr/bin/python3

import boto3

class DyanomoDbObjectList:
    CURRENT_ITEM_FORMAT = 2

    def __init__(self, table_name, region):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def add_object(self, object_name, dic):
        self.table.put_item(
            Item={
                'object-name': object_name,
                'size': dic['size'],  # new in format 1
                'md5': dic['md5'],  # new in format 1
                'sha1_4k': dic['sha1_4k'],  # new in format 2
                'sha1_1m': dic['sha1_1m'],  # new in format 2
                'item-format': self.CURRENT_ITEM_FORMAT,
            }
        )

    def is_object_exist(self, object_name, dic):
        response = self.table.get_item(
            Key={
                'object-name': object_name,
            }
        )

        if 'Item' in response:
            self.__update_metadata_version(object_name, dic, response)
            return True
        else:
            return False

    def __update_metadata_version(self, object_name, dic, response):
        """If object's info (the DynamoDB item) is out of dated, update it"""
        format_version = response['Item'].get('item-format') or 0
        if format_version < self.CURRENT_ITEM_FORMAT:
            self.add_object(object_name, dic)
            print("    DynamoDB item format updated.")


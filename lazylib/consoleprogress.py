#!/usr/bin/env python3

import sys

class ConsoleProgress:
    def __init__(self, con=sys.stderr):
        self.con = con
        self.last_msg_len = 0

    def clear(self, new_msg_len):
        if new_msg_len < self.last_msg_len:
            mask = " " * self.last_msg_len
            print(mask + "\r", file=self.con, end="")

    def update(self, msg):
        self.clear(len(msg))
        self.last_msg_len = len(msg)
        print(msg + "\r", file=self.con, end="")

    def print(self, msg):
        self.clear(len(msg))
        self.last_msg_len = 0
        print(msg, file=self.con)

    @staticmethod
    def main():
        c = ConsoleProgress()
        c.update("Update test 1  (this message should not be seen)")
        c.update("Update test 2")
        c.print("Print 1")
        c.print("Print 2")

if __name__ == "__main__":
    ConsoleProgress.main()


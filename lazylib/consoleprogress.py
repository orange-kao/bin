#!/usr/bin/env python3

import sys
import time

class ConsoleProgress:
    def __init__(self, con=sys.stderr, cursor_at_the_end=False):
        self.con = con
        self.last_msg_len = 0
        self.cursor_at_the_end = cursor_at_the_end

    def clear(self, new_msg_len):
        if new_msg_len < self.last_msg_len:
            mask = " " * self.last_msg_len
            if self.cursor_at_the_end:
                print("\r" + mask, file=self.con, end="")
            else:
                print(mask + "\r", file=self.con, end="")

    def update(self, msg):
        self.clear(len(msg))
        self.last_msg_len = len(msg)
        if self.cursor_at_the_end:
            print("\r" + msg, file=self.con, end="")
        else:
            print(msg + "\r", file=self.con, end="")

    def print(self, msg):
        self.clear(len(msg))
        self.last_msg_len = 0
        if self.cursor_at_the_end:
            print("\r" + msg, file=self.con)
        else:
            print(msg, file=self.con)

    @staticmethod
    def main():
        for cursor_at_the_end in [False, True]:
            print(f"cursor_at_the_end is {cursor_at_the_end}")
            c = ConsoleProgress(cursor_at_the_end=cursor_at_the_end)
            for i in range(0,10):
                c.update(f"Update {i}")
                time.sleep(0.2)
            for i in range(0,10):
                c.print(f"Print {i}")
                time.sleep(0.2)

if __name__ == "__main__":
    ConsoleProgress.main()


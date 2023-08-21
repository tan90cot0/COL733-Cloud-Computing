from __future__ import annotations

import logging
from typing import Optional, Final

from redis.client import Redis

from base import Worker
from constants import IN, COUNT, FNAME


class MyRedis:
  def __init__(self):
    self.rds: Final = Redis(host='localhost', port=6379, password='pass',
                       db=0, decode_responses=False)
    self.rds.flushall()
    self.rds.xgroup_create(IN, Worker.GROUP, id="0", mkstream=True)

  def add_file(self, fname: str):
    self.rds.xadd(IN, {FNAME: fname})

  def get_file(self, consumer_group: string, consumer_name: string, stream_name: bytes):
    path_ds = self.rds.xreadgroup(consumer_group, consumer_name, {stream_name:'>'}, count = 1, noack = True)
    if len(path_ds)==0:
      return [], False
    else:
      return path_ds[0][1][0][1][FNAME].decode(), True

  def top(self, n: int) -> list[tuple[bytes, float]]:
    return self.rds.zrevrangebyscore(COUNT, '+inf', '-inf', 0, n,
                                     withscores=True)

  def update_cnt(self, cnt: int, word: string) -> None:
    self.rds.zincrby(COUNT, cnt, word.encode())

  def get_size(self)->int:
    return self.rds.zcard(COUNT)
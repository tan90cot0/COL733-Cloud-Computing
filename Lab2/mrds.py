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

  def get_file(self, consumer_group: str, consumer_name: str, stream_name: bytes):
    path_ds = self.rds.xreadgroup(groupname=consumer_group, 
                                  consumername=consumer_name, 
                                  streams = {stream_name:'>'}, 
                                  count = 1)
    if len(path_ds)==0:
      return self.get_others_file(consumer_group, stream_name, consumer_name)
    else:
      return path_ds[0][1][0][1][FNAME].decode(), True, path_ds[0][1][0][0]
    
  def get_others_file(self, consumer_group, stream_name, consumer_name):
    # Set the min idle time
    claimed_messages = self.rds.xautoclaim(name = stream_name, 
                                           groupname=consumer_group, 
                                           consumername=consumer_name, 
                                           min_idle_time=0,
                                           count=1)
    if claimed_messages[1]:
      return claimed_messages[1][0][1][FNAME].decode(), True, claimed_messages[1][0][0]
    else:
      return [], False, None

  def top(self, n: int) -> list[tuple[bytes, float]]:
    return self.rds.zrevrangebyscore(COUNT, '+inf', '-inf', 0, n,
                                    withscores=True)

  def update_cnt(self, count_dict, id, stream, grp) -> None:
    keys = list(count_dict.keys())
    vals = list(count_dict.values())
    num = len(keys)

    # Run the lua script atomically
    self.rds.fcall('mylib', 5+2*num, id, stream, grp ,COUNT, num, *keys, *vals)

  def get_size(self)->int:
    return self.rds.zcard(COUNT)
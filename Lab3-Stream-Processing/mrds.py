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
    self.file_map = {}

  def get_timestamp(self) -> float:
    timestamp = self.rds.time()
    return float(f'{timestamp[0]}.{timestamp[1]}')

  def add_file(self, fname: str) -> None:
    id = self.rds.fcall('add_file', 3, fname, IN, FNAME)
    self.file_map[id.decode()] = fname
    # id = self.rds.xadd(IN, {FNAME: fname})
    # self.rds.hset('latency', id, self.get_timestamp())

  def top(self, n: int) -> list[tuple[bytes, float]]:
    return self.rds.zrevrangebyscore(COUNT, '+inf', '-inf', 0, n,withscores=True)

  def get_latency(self) -> list[float]:
    lat = []
    lat_data = self.rds.hgetall("latency")
    for k in sorted(lat_data.keys()):
      v = lat_data[k]
      lat.append(float(v.decode()))
    return lat
  
  def write_to_file(self):
    lat = []
    f = open("c0.txt", "a")
    lat_data = self.rds.hgetall("latency")
    for k in sorted(lat_data.keys()):
      v = lat_data[k]
      f.write(self.file_map[k.decode()][24:-4] + ', ' + lat_data[k].decode() + '\n')
    f.close()

  def read(self, worker: Worker) -> Optional[tuple[bytes, dict[bytes, bytes]]]:
    claimed_messages = self.rds.xautoclaim(name = IN, 
                                           groupname=Worker.GROUP, 
                                           consumername=worker.name, 
                                           min_idle_time=500,
                                           count=1)
    if claimed_messages[1]:
      return claimed_messages[1][0]
    else:
      path_ds = self.rds.xreadgroup(groupname=Worker.GROUP, 
                                  consumername=worker.name, 
                                  streams = {IN:'>'}, 
                                  count = 1)
      if len(path_ds)==0:
        return None, None
      else:
        return path_ds[0][1][0]

  def write(self, id: bytes, wc: dict[str, int]) -> None:
    keys = list(wc.keys())
    vals = list(wc.values())
    num = len(keys)

    # Run the lua script atomically
    in_time = float(self.rds.hget('latency', id).decode())
    self.rds.fcall('add_wc', 5+2*num, id, IN, Worker.GROUP ,COUNT, num, *keys, *vals)
    out_time = float(self.rds.hget('latency', id).decode())
    # out_time = self.get_timestamp()
    # in_time = float(self.rds.hget('latency', id).decode())
    # latency = out_time-in_time
    # print(latency, out_time, in_time)
    # self.rds.hset('latency', id, latency)

  def is_pending(self):
    pending_info = self.rds.xpending(IN, Worker.GROUP)
    return pending_info['pending']!=0

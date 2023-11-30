from __future__ import annotations
import logging
from redis.client import Redis
from base import Worker
from constants import IN, COUNT, FNAME, IS_RAFT, N_NORMAL_WORKERS, RAFT_PORTS
import subprocess
import time
import os

class MyRedis:
  def __init__(self):

    if IS_RAFT:
      self.rds = Redis(host='localhost', port=RAFT_PORTS[0],
                      db=0, decode_responses=False)
    else:
      self.rds = Redis(host='localhost', port=6379, password='pass',
                        db=0, decode_responses=False)
      self.rds.flushall()
      self.rds.xgroup_create(IN, Worker.GROUP, id="0", mkstream=True)

  def add_file(self, fname: str):
    self.rds.xadd(IN, {FNAME: fname})

  def get_file(self, consumer_name: str):
    try:
      path_ds = self.rds.xreadgroup(groupname=Worker.GROUP,
                                    consumername=consumer_name, 
                                    streams = {IN:'>'}, 
                                    count = 1)
      if len(path_ds)==0:
        claimed_messages = self.rds.xautoclaim(name = IN, 
                                            groupname=Worker.GROUP, 
                                            consumername=consumer_name, 
                                            min_idle_time=0,
                                            count=1)
        if claimed_messages[1]:
          return claimed_messages[1][0][1][FNAME].decode(), True, claimed_messages[1][0][0]
        else:
          return [], False, None
      else:
        return path_ds[0][1][0][1][FNAME].decode(), True, path_ds[0][1][0][0]
    except:
      time.sleep(0.1)
      return self.get_file(consumer_name)

  def top(self, n: int) -> list[tuple[bytes, float]]:
    return self.rds.zrevrangebyscore(COUNT, '+inf', '-inf', 0, n, withscores=True)

  def update_cnt(self, count_dict, id) -> None:
    keys = list(count_dict.keys())
    vals = list(count_dict.values())
    num = len(keys)
    try:
      self.rds.fcall('mylib', 5+2*num, id, IN, Worker.GROUP ,COUNT, num, *keys, *vals)
    except:
      time.sleep(0.1)
      self.update_cnt(count_dict, id)

  def update_cnt_raft(self, count_dict):
    top10 = []
    for k, v in count_dict.items():
      top10.append([v, k])
    top10.sort()
    top10.reverse()
    for i in range(10):
      while(True):
        try: 
          self.rds.zincrby(COUNT, top10[i][0], top10[i][1])
          break
        except:
          time.sleep(0.1)

  def get_size(self)->int:
    return self.rds.zcard(COUNT)
  
  def is_pending(self):
    try:
      pending_info = self.rds.xpending(IN, Worker.GROUP)
      return pending_info['pending']!=0
    except:
      time.sleep(0.1)
      return self.is_pending()
    
  def restart(self, down_time=1, down_port=-1, instance_port=-1):

    if IS_RAFT:

      if os.system(f"sudo kill -9 $(ps aux | grep {down_port} | head -1 | awk '{{print $2}}')")!=0:
        print('did not kill the process on the down port')
      else:
        self.rds = Redis(host='localhost', port=instance_port, db=0, decode_responses=False)
        time.sleep(down_time)
        os.system(f'redis-server --port {down_port} --dbfilename raft{down_port}.rdb --loadmodule /home/baadalvm/redisraft/redisraft.so --raft.log-filename raftlog{down_port}.db --raft.follower-proxy yes --raft.addr localhost:{down_port} --daemonize yes')
        time.sleep(2)

    else:

      try:
          subprocess.run(['sudo', 'systemctl', 'stop', 'redis-server'])
      except subprocess.CalledProcessError as e:
          print(f"Error stopping Redis: {e}")

      time.sleep(down_time)

      try:
          subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'])
          # subprocess.run(["redis-cli", "config", "set", "requirepass", "pass"])
      except subprocess.CalledProcessError as e:
          print(f"Error starting Redis: {e}")

  def checkpoint(self):
    try:
      while self.is_pending():
        time.sleep(1)
        self.rds.bgsave()
    except:
      time.sleep(0.1)
      self.checkpoint()

  def get_flag(self):
    try:
      return int(self.rds.get('flag'))
    except:
      time.sleep(0.1)
      self.get_flag()

  def update_flag(self):
    try:
      self.rds.incr('flag')
    except:
      time.sleep(0.1)
      self.update_flag()

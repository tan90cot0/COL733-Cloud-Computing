from typing import Any
from base import Worker
from mrds import MyRedis
from constants import IS_RAFT
import pandas as pd
import os

class WcWorker(Worker):

  def count(self, path):
    count_dict = {}
    tweets = pd.read_csv(path, lineterminator='\n')
    tweets["text"] = tweets["text"].astype(str)
    for text in tweets.loc[:,"text"]:
      if text == '\n':
          continue
      for word in text.split(" "):
          if word not in count_dict:
              count_dict[word] = 0
          count_dict[word] = count_dict[word] + 1
    return count_dict
  
  def get_path_list(self, kwargs):
    worker_id = kwargs['worker_id']
    data_dir = kwargs['data_dir']
    n_workers = kwargs['workers_cnt']
    if data_dir[-1]!='/':
      data_dir+='/'
    return [data_dir+f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f)) and len(f)>8 and int(f[5:-4])%n_workers==worker_id]

  def run(self, **kwargs: Any) -> None:
    rds: MyRedis = kwargs['rds']
    if IS_RAFT:
      for path in self.get_path_list(kwargs):
        count_dict = self.count(path)
        rds.update_cnt_raft(count_dict)
      rds.update_flag()
    else:
      path, res, id = rds.get_file(self.name)
      while res:
        count_dict = self.count(path)
        top10 = []
        for k, v in count_dict.items():
          top10.append([v, k])
        top10.sort()
        top10.reverse()
        count_dict = {k:v for v, k in top10[:10]}
        rds.update_cnt(count_dict, id)
        path, res, id = rds.get_file(self.name)

    
      

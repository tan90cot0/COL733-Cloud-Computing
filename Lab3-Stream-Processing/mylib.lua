#!lua name=mylib

local function add_wc(keys, args)
  -- keys = id, stream, grp, count, num, words, counts
  local id = keys[1]
  if redis.call('xack', keys[2], keys[3], id)==1 then
    for i = 1, keys[5] do
      redis.call('zincrby', keys[4], keys[5+keys[5]+i], keys[5+i])
    end
    local serverTime = redis.call('TIME')
    local seconds = tonumber(serverTime[1])
    local microseconds = tonumber(serverTime[2])
    local out_time = seconds + microseconds / 1000000

    local in_time = redis.call('HGET', 'latency', id)
    redis.call('HSET', 'latency', id, out_time-in_time)
  end
end

local function add_file(keys)
  local stream = keys[2]

  local id = redis.call("XADD", stream, '*', keys[3], keys[1])
  local serverTime = redis.call('TIME')
  local seconds = tonumber(serverTime[1])
  local microseconds = tonumber(serverTime[2])
  local in_time = seconds + microseconds / 1000000
  redis.call('HSET', 'latency', id, in_time)
  return id
end

redis.register_function('add_wc', add_wc)
redis.register_function('add_file', add_file)

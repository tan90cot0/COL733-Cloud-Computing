#!lua name=mylib

local function mylib(keys) 

  -- keys = id, stream, grp, count, num, words, counts
  if redis.call('xack', keys[2], keys[3], keys[1])==1 then
    for i = 1, keys[5] do
      redis.call('zincrby', keys[4], keys[5+keys[5]+i], keys[5+i])
    end
  end

end

redis.register_function('mylib', mylib)
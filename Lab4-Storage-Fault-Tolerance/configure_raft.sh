# sudo killall redis-server
# sudo systemctl stop redis-server

rm *.db
rm *.db.meta
rm *.db.idx

sudo killall redis-server

leader_port="$1"

redis-server \
    --port $leader_port --dbfilename raft$leader_port.rdb \
    --loadmodule /home/baadalvm/redisraft/redisraft.so \
    --raft.log-filename raftlog$leader_port.db \
    --raft.addr localhost:$leader_port --daemonize yes --raft.follower-proxy yes
sleep 5
redis-cli -p $leader_port raft.cluster init

shift
while [ $# -gt 0 ]; do
    follower_port="$1"
    redis-server \
    --port $follower_port --dbfilename raft$follower_port.rdb \
    --loadmodule /home/baadalvm/redisraft/redisraft.so \
    --raft.log-filename raftlog$follower_port.db \
    --raft.addr localhost:$follower_port --daemonize yes --raft.follower-proxy yes
    sleep 1
    redis-cli -p $follower_port RAFT.CLUSTER JOIN localhost:$leader_port
    shift
done
# COL733-Cloud-Computing

This is a distributed word count application. We start stateless python processes to act as distributed workers. These workers will co-ordinate with each other through Redis. Redis behaves like the master (or driver program) in contemporary systems.

All workers have access to a shared file system for reading and writing large inputs. This is trivially true on our single system. In a real setup, workers would additionally use a distributed file system like HDFS or a blob store like S3.

## Lab 1: Parallel Execution
In this lab, we will make the word count application run end-to-end using Redis.

1. Update GLOB in constants.py to point to your data folder. 
2. Run python3 client.py. 

The basic file structure is as follows:

1. client.py iterates over the folder with the text files to add the file paths into a redis stream using xadd. It then starts the worker processes.
2. Worker processes do xreadgroup to read one file name from the Redis stream. Call xreadgroup such that each worker gets a different file name.
3. Worker process reads the file it is supposed to work on and counts each word’s frequency.
4. When done, the worker process can use zincrby to increment each word’s count in a redis sorted set. And finally xack the message containing the filename.
Then it reads another file by again calling xreadgroup. If there are no more files to process, it exits.

## Lab 2: Fault Tolerance of Workers
Now we wish to ensure that our system is tolerant to worker failures. Since, workers are stateless, we should be ok with losing worker state. But, we still have to ensure two things:

1. Updates to redis should be made atomic. If a worker crashes after incrementing counts of only a few words, then we will end up with incorrect counts. (We use Redis fcall to xack a file and to increment word counts as one atomic operation.)
2. Consumer groups in Redis streams ensure that each worker gets a unique file name. But, if a worker crashes after getting a file name from Redis stream, that file’s words may never get counted. Therefore, other workers will have to steal filenames that have not been xacked till a timeout. (We use xautoclaim to do so.)

## Lab 3: Stream Processing
Our implementation already supports micro-batching approach to streaming. In this lab, we modify the client program to inject a certain number of files containing tweets to the redis stream every second. These files can be thought of as a micro-batch.

What we do in this lab is measure the latency of each file i.e, the time from injecting the file into the stream to the time when file was processed successfully.

We draw a timeline of this latency at different injection rates, in the presence of failed workers, and stragglers. We see that when workers fail (or become slow), the latency temporarily goes up, but then it recovers.

## Lab 4: Redis FT
### Using Checkpoints
We would like to now ensure that our system tolerates Redis failures. To reason about correctness, note that a Redis instance handles one command after another in a single thread to keep it linearizable.

In this lab, we will periodically create a checkpoint using the BGSAVE command. Redis starts periodically storing a dump.rdb file on disk.

You can run CONFIG GET dir from redis-cli to find the directory where dump.rdb gets stored. You may try to crash the Redis instance and then start a new Redis instance. Redis should automatically read dump.rdb file and restore from it. Verify that this new instance have the keys from the old instance by running keys * using redis-cli.

Now while the job is running, try crashing the Redis instance and restarting another one. From a correctness standpoint, checkpoints are consistent because Redis has a single event loop and because all our edits were made atomic in lab 2.

In other words, let us say that a file foo was processed after the checkpoint. Now after a failover, the new Redis instance (recovered from the checkpoint) will remember that the file has NOT yet been xacked. Therefore, a worker will again receive the file for processing and it will again xack + increment word counts in one atomic operation. Since our workers are stateless and file counts are deterministic, recomputing a file’s word counts are ok.

Ensure that you set up the new instance in an identical manner, i.e, listen on the same port, set up the same password, and insert the same lua functions.


### Using Synchronous Replication
Here, we create 2f+1 Redis replicas and connect them with Raft using the RedisRaft module. The replicas are always kept consistent by doing the replication synchronously. In other words, the leader does not return from a Redis command until it hears back an acknowledgement from a majority of replicas.

Try arbitrarily crashing and restarting f replicas while the job is running and observe that the job finishes successfully. The good thing about this design is that we never have to recompute a file (rollback computation) after failovers. But the bad thing is that during normal operations (without Redis failures), each Redis write operation is now slower because of the added overhead of replicating logs.
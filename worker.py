import os
import redis
from rq import Worker, Queue, Connection

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
listen = ['high', 'default', 'low']

if __name__ == '__main__':
	print('Worker running')
	with Connection(conn):
		worker = Worker(map(Queue, listen))
		worker.work()
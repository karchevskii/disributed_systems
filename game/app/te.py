from redis import Redis

r = Redis(host='localhost', port=6379, password="password", decode_responses=True)

r.set('foo', 'bar')
print(r.get('foo'))
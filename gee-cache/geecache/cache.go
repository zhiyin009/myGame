package geecache

import (
	"exmaple/geecache/lru"
	"sync"
)

type cache struct {
	mu         sync.Mutex
	lru        *lru.Cache
	cacheBytes int64
}

func (c *cache) add(key string, value ByteView) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.lru == nil {
		c.lru = lru.New(0, nil)
	}
	c.lru.Add(key, value)
}

func (c *cache) get(key string) (bv ByteView, ok bool) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.lru == nil {
		return
	}

	if e, ok := c.lru.Get(key); ok {
		bv = e.(ByteView)
		return bv, true
	}

	return
}

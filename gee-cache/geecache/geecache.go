package geecache

import (
	"fmt"
	"log"
	"sync"
)

type Getter interface {
	Get(key string) ([]byte, error)
}

type GetterFunc func(key string) ([]byte, error)

func (f GetterFunc) Get(key string) ([]byte, error) {
	return f(key)
}

type Group struct {
	name      string
	getter    Getter
	mainCache cache
	peers     PeerPicker
}

var (
	mu     sync.RWMutex
	groups = make(map[string]*Group)
)

func NewGroup(name string, cacheBytes int64, getter Getter) *Group {
	if getter == nil {
		panic("nil getter")
	}
	mu.Lock()
	defer mu.Unlock()

	g := &Group{
		name:      name,
		getter:    getter,
		mainCache: cache{cacheBytes: cacheBytes},
	}

	groups[name] = g
	return g
}

func GetGroup(name string) *Group {
	mu.RLock()
	g := groups[name]
	mu.RUnlock()
	return g
}

func (g *Group) Get(key string) (ByteView, error) {
	if key == "" {
		return ByteView{}, fmt.Errorf("key is requried")
	}

	if bv, ok := g.mainCache.get(key); ok {
		log.Println("[GeeCache] hit")
		return bv, nil
	}

	return g.load(key)
}

func (g *Group) RegisterPeers(peers PeerPicker) {
	if g.peers != nil {
		panic("RegisterPeerPicker called more than once")
	}
	g.peers = peers
}

func (g *Group) load(key string) (bv ByteView, err error) {
	if g.peers != nil {
		if peer, ok := g.peers.PickPeer(key); ok {
			if bv, err = g.getFromPeer(peer, key); err == nil {
				return bv, nil
			}
			log.Println("[GeeCache] Failed to get from peer", err)
		}
	}

	return g.loadLocally(key)
}

func (g *Group) getFromPeer(peer PeerGetter, key string) (ByteView, error) {
	bytes, err := peer.Get(g.name, key)
	if err != nil {
		return ByteView{}, err
	}
	return ByteView{b: bytes}, nil
}

func (g *Group) loadLocally(key string) (ByteView, error) {
	b, err := g.getter.Get(key)
	if err != nil {
		return ByteView{}, err
	}

	res := ByteView{cloneBytes(b)}
	g.populateCache(key, res)
	return res, nil
}

func (g *Group) populateCache(key string, value ByteView) {
	g.mainCache.add(key, value)
}

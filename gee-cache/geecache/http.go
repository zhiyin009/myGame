package geecache

import (
	"example/geecache/consistenthash"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
)

const defaultBasePath = "/api/"
const defaultReplicas = 50

type HTTPPool struct {
	addr        string
	basePath    string
	mu          sync.Mutex
	peers       *consistenthash.Map
	httpGetters map[string]*httpGetter
}

func (p *HTTPPool) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if !strings.HasPrefix(r.URL.Path, p.basePath) {
		http.Error(w, "HTTPPool serving unexpected path: "+r.URL.Path, http.StatusBadRequest)
		return
	}
	log.Println(r.Method, r.URL.Path)

	parts := strings.SplitN(r.URL.Path[len(p.basePath):], "/", 2)
	if len(parts) != 2 {
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	g := GetGroup(parts[0])
	if g == nil {
		http.Error(w, "Invalid group "+parts[0], http.StatusBadRequest)
		return
	}

	v, err := g.Get(parts[1])
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	//w.Header().Set("Content-Type", "application/octet-stream")
	w.Write(v.b)
}

func (p *HTTPPool) Set(peers ...string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	p.peers = consistenthash.New(defaultReplicas, nil)
	p.peers.Add(peers...)
	p.httpGetters = make(map[string]*httpGetter, len(peers))
	for _, peer := range peers {
		p.httpGetters[peer] = &httpGetter{peer}
	}
}

func (p *HTTPPool) PickPeer(key string) (PeerGetter, bool) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if peer := p.peers.Get(key); peer != "" && peer != p.addr {
		p.Log("Pick peer %s", peer)
		return p.httpGetters[peer], true
	}

	return nil, false
}

var _ PeerPicker = (*HTTPPool)(nil)

func NewHTTPPool(addr string) *HTTPPool {
	return &HTTPPool{
		addr:     addr,
		basePath: defaultBasePath,
	}
}

func (p *HTTPPool) Log(format string, v ...interface{}) {
	log.Printf("[Server %s] %s", p.addr, fmt.Sprintf(format, v...))
}

type httpGetter struct {
	baseUrl string
}

func (g *httpGetter) Get(group string, key string) ([]byte, error) {
	u := fmt.Sprintf(
		"%v%v%v",
		g.baseUrl,
		url.QueryEscape(group),
		url.QueryEscape(key))

	res, err := http.Get(u)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("server returned: %v", res.StatusCode)
	}

	bytes, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("reading response body: %v", err)
	}

	return bytes, nil
}

var _ PeerGetter = (*httpGetter)(nil)

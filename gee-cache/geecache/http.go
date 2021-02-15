package geecache

import (
	"example/geecache/consistenthash"
	pb "example/geecache/geecachepb"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"path"
	"strings"
	"sync"

	"github.com/golang/protobuf/proto"
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

	view, err := g.Get(parts[1])
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	body, err := proto.Marshal(&pb.Response{Value: view.ByteSlice()})
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Write(body)
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

func (h *httpGetter) Get(in *pb.Request, out *pb.Response) (error) {
	u, err := url.ParseRequestURI(h.baseUrl)
	if err != nil {
		panic(err)
	}

	u.Path = path.Join(u.Path, in.Group, in.Key)
	res, err := http.Get(u.String())
	if err != nil {
		return err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("server returned: %v", res.StatusCode)
	}
	fmt.Printf("[Remote Server %s] Got %s/%s Success\n", h.baseUrl, in.Group, in.Key)

	bytes, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return fmt.Errorf("reading response body: %v", err)
	}

	if err = proto.Unmarshal(bytes, out); err != nil {
		return fmt.Errorf("decoding response body: %v", err)
	}

	return nil
}

var _ PeerGetter = (*httpGetter)(nil)

package geecache

import (
	"log"
	"net/http"
	"strings"
)

const defaultBasePath = "/api/"

type HTTPPool struct {
	addr     string
	basePath string
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

func NewHTTPPool(addr string) *HTTPPool {
	return &HTTPPool{
		addr:     addr,
		basePath: defaultBasePath,
	}
}

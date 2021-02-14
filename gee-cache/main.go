package main

import (
	"example/geecache"
	"flag"
	"fmt"
	"log"
	"net/http"
	"net/url"
)

var db = map[string]string{
	"Tom":    "630",
	"Jack":   "589",
	"Sam":    "567",
	"Xiaozy": "620",
}

const BasePath = "/api/"

func createGroup() *geecache.Group {
	return geecache.NewGroup("score", 8*1024*1024, geecache.GetterFunc(
		func(key string) ([]byte, error) {
			log.Println("[SlowDB] search key", "key")
			if score, ok := db[key]; ok {
				return []byte(score), nil
			}
			return nil, fmt.Errorf("%s not exist", key)
		}))
}

func startCacheServer(addr string, addrs []string, gee *geecache.Group) {
	peers := geecache.NewHTTPPool(addr)
	peers.Set(addrs...)
	gee.RegisterPeers(peers)
	u, err := url.Parse(addr)
	if err != nil {
		log.Fatal(err)
	}

	log.Println("geecache is running at", u.Host)
	log.Fatal(http.ListenAndServe(u.Host, peers))
}

func startApiServer(apiAddr string, gee *geecache.Group) {
	http.Handle(BasePath, http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			key := r.URL.Query().Get("key")
			view, err := gee.Get(key)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			//w.Header().Set("Content-Type", "application/octet-stream")
			w.Write(view.ByteSlice())

		}))
	log.Println("fontend server is running at", apiAddr)
	log.Fatal(http.ListenAndServe(apiAddr[7:], nil))
}

func main() {
	var port int
	var api bool
	flag.IntVar(&port, "port", 8001, "Geecache server port")
	flag.BoolVar(&api, "api", false, "Start a api server?")
	flag.Parse()

	apiAddr := "http://localhost:8080"
	addrMap := map[int]string{
		8001: "http://localhost:8001/api/",
		8002: "http://localhost:8002/api/",
		8003: "http://localhost:8003/api/",
	}

	var addrs []string
	for _, v := range addrMap {
		addrs = append(addrs, v)
	}

	gee := createGroup()
	if api {
		go startApiServer(apiAddr, gee)
	}
	startCacheServer(addrMap[port], addrs, gee)
}

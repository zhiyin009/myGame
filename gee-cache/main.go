package main

import (
	"example/geecache"
	"fmt"

	"log"
	"net/http"
)

var db = map[string]string{
	"Tom":  "630",
	"Jack": "589",
	"Sam":  "567",
}

func main() {
	geecache.NewGroup("score", 8*1024*1024, geecache.GetterFunc(
		func(key string) ([]byte, error) {
			log.Println("[SlowDB] search key", "key")
			if score, ok := db[key]; ok {
				return []byte(score), nil
			}
			return nil, fmt.Errorf("%s not exist", key)
		}))

	addr := "127.0.0.1:8080"
	peers := geecache.NewHTTPPool(addr)
	log.Println("server listening on:", addr)
	http.ListenAndServe(addr, peers)
}

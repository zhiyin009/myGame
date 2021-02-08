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

type Nothing struct{}

func (*Nothing) ServeHTTP(writer http.ResponseWriter, request *http.Request) {
	log.Println(request.Method)
	writer.Write([]byte("HelloWord"))
}

func main() {
	fmt.Println("I am fine")
	_ = geecache.NewGroup("score", 8*1024*1024, geecache.GetterFunc(func(key string) ([]byte, error) {
		return []byte("fff"), nil
	}))

	http.ListenAndServe("127.0.0.1:8080", &Nothing{})
}

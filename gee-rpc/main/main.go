package main

import (
	"fmt"
	"geerpc"
	"log"
	"net"
	"sync"
	"time"
)

func startServer(addr chan string) {
	l, err := net.Listen("tcp4", ":0")
	if err != nil {
		log.Fatal("network error:", err)
	}

	log.Println("start rpc server on:", l.Addr())
	addr <- l.Addr().String()
	geerpc.Accept(l)
}

//func main() {
//	addr := make(chan string)
//	go startServer(addr)
//
//	time.Sleep(time.Second)
//	conn, _ := net.Dial("tcp4", <-addr)
//	defer func() { _ = conn.Close() }()
//
//	_ = json.NewEncoder(conn).Encode(geerpc.DefaultOption)
//	cc := codec.NewCodecFuncMap[codec.GobType](conn)
//	for i := 0; i < 5; i++ {
//		h := &codec.Header{
//			ServiceMethod: "test",
//			Seq:           uint64(i),
//		}
//
//		cc.Write(h, "echo test")
//		if err := cc.ReadHeader(h); err != nil {
//			log.Println(err)
//		}
//		var reply string
//		if err := cc.ReadBody(&reply); err != nil {
//			log.Println(err)
//		}
//
//		log.Println("reply:", reply)
//	}
//}
func main() {
	log.SetFlags(0)
	addr := make(chan string)
	go startServer(addr)
	client, _ := geerpc.Dial("tcp", <-addr)
	defer func() { _ = client.Close() }()

	time.Sleep(1 * time.Second)
	// send request & receive response
	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			args := fmt.Sprintf("geerpc req %d", i)
			var reply string
			if err := client.Call("Foo.Sum", args, &reply); err != nil {
				log.Fatal("call Foo.Sum error:", err)
			}
			log.Println("reply:", reply)
		}(i)
	}
	wg.Wait()
}

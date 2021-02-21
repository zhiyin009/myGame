package geerpc

import (
	"encoding/json"
	"fmt"
	"geerpc/codec"
	"io"
	"log"
	"net"
	"reflect"
	"sync"
)

const MagicNumber = 0x3bef5c

type Option struct {
	MagicNumber int        // MagicNumber marks this's a geerpc request
	CodecType   codec.Type // client may choose different Codec to encode body
}

var DefaultOption = &Option{
	MagicNumber: MagicNumber,
	CodecType:   codec.GobType,
}

type Server struct{}

var DefaultServer = Server{}

type request struct {
	h      *codec.Header
	argv   reflect.Value
	replyv reflect.Value
}

func (s *Server) Accept(list net.Listener) {
	for {
		conn, err := list.Accept()
		if err != nil {
			log.Println("rpc server: accept error:", err)
			return
		}
		go s.ServerConn(conn)
	}
}

func Accept(list net.Listener) {
	DefaultServer.Accept(list)
}

func (s *Server) ServerConn(conn net.Conn) {
	defer func() { _ = conn.Close() }()

	opt := &Option{}
	if err := json.NewDecoder(conn).Decode(opt); err != nil {
		log.Println("rpc server: connect error:", err)
		return
	}

	if opt.MagicNumber != MagicNumber {
		log.Printf("rpc server: Invelid MagicNumber %s from %s", opt.MagicNumber, conn.RemoteAddr())
		return
	}

	f := codec.NewCodecFuncMap[opt.CodecType]
	if f == nil {
		log.Printf("rpc server: invalid codec type %s from %s", opt.CodecType, conn.RemoteAddr())
		return
	}

	s.serverCodec(f(conn))
}

var invalidRequest = struct{}{}

func (s *Server) serverCodec(cc codec.Codec) {
	sending := new(sync.Mutex)
	wg := new(sync.WaitGroup)

	for {
		req, err := s.readRequest(cc)
		if err != nil {
			if req == nil {
				break // it's not possible to recover, so close the connection
			}

			req.h.Error = err.Error()
			s.sendResponse(cc, req.h, invalidRequest, sending)
			continue
		}

		wg.Add(1)
		go s.handleRequest(cc, req, sending, wg)
	}

	wg.Wait()
	_ = cc.Close()
}

func (s *Server) readRequestHeader(cc codec.Codec) (*codec.Header, error) {
	h := &codec.Header{}
	if err := cc.ReadHeader(h); err != nil {
		if err != io.EOF && err != io.ErrUnexpectedEOF {
			log.Println("rpc server: read header error:", err)
		}
		return nil, err
	}

	return h, nil
}

func (s *Server) readRequest(cc codec.Codec) (*request, error) {
	h, err := s.readRequestHeader(cc)
	if err != nil {
		return nil, err
	}

	req := &request{h: h}
	req.argv = reflect.New(reflect.TypeOf(""))
	if err := cc.ReadBody(req.argv.Interface()); err != nil {
		log.Println("rpc server: read argv err:", err)
	}

	return req, nil
}

func (s *Server) sendResponse(cc codec.Codec, header *codec.Header, body interface{}, sending *sync.Mutex) {
	sending.Lock()
	defer sending.Unlock()

	if err := cc.Write(header, body); err != nil {
		log.Println("rpc server: send response err:", err)
	}
}

func (s *Server) handleRequest(cc codec.Codec, req *request, sending *sync.Mutex, wg *sync.WaitGroup) {
	defer wg.Done()
	log.Println(req.h, req.argv.Elem())
	req.replyv = reflect.ValueOf(fmt.Sprintf("geerpc resp %d", req.h.Seq))
	s.sendResponse(cc, req.h, req.replyv.Interface(), sending)
}

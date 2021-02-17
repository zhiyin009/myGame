package codec

import (
	"bufio"
	"encoding/gob"
	"fmt"
	"io"
)

type GobCodec struct {
	conn io.ReadWriteCloser
	buf  *bufio.Writer
	dec  *gob.Decoder
	enc  *gob.Encoder
}

var _ Codec = (*GobCodec)(nil)

func NewGobCodec(conn io.ReadWriteCloser) Codec {
	buf := bufio.NewWriter(conn)
	return &GobCodec{
		conn: conn,
		buf:  buf,
		dec:  gob.NewDecoder(conn),
		enc:  gob.NewEncoder(buf),
	}
}

func (g *GobCodec) ReadHeader(h *Header) error {
	return g.dec.Decode(h)
}

func (g *GobCodec) ReadBody(b interface{}) error {
	return g.dec.Decode(b)
}

func (g *GobCodec) Write(h *Header, b interface{}) (err error) {
	defer func() {
		_ = g.buf.Flush()
		if err != nil {
			_ = g.Close()
		}
	}()

	if err := g.enc.Encode(h); err != nil {
		fmt.Println("rpc codec: gob error encoding header:", h)
		return err
	}

	if err := g.enc.Encode(b); err != nil {
		fmt.Println("rpc codec: gob error encoding body:", b)
		return err
	}

	return nil
}

func (g *GobCodec) Close() error {
	return g.conn.Close()
}

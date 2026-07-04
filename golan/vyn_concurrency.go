package main

import "C"
import (
	"sync"
	"unsafe"
	"strconv"
)

type vynChannel struct {
	ch     chan interface{}
	closed bool
	mu     sync.Mutex
}

var channels = struct {
	mu   sync.Mutex
	data map[int]*vynChannel
	next int
}{data: make(map[int]*vynChannel)}

var goroutineCallbacks = struct {
	mu    sync.Mutex
	queue []goroutineCall
}{}

type goroutineCall struct {
	fnID    int
	argJSON string
}

//export vyn_chan_new
func vyn_chan_new(bufSize C.int) C.int {
	channels.mu.Lock()
	defer channels.mu.Unlock()
	channels.next++
	channels.data[channels.next] = &vynChannel{
		ch: make(chan interface{}, int(bufSize)),
	}
	return C.int(channels.next)
}

//export vyn_chan_send_int
func vyn_chan_send_int(chanID C.int, val C.long) C.int {
	channels.mu.Lock()
	c, ok := channels.data[int(chanID)]
	channels.mu.Unlock()
	if !ok {
		return -1
	}
	c.mu.Lock()
	if c.closed {
		c.mu.Unlock()
		return -2
	}
	c.mu.Unlock()
	c.ch <- int64(val)
	return 0
}

//export vyn_chan_send_float
func vyn_chan_send_float(chanID C.int, val C.double) C.int {
	channels.mu.Lock()
	c, ok := channels.data[int(chanID)]
	channels.mu.Unlock()
	if !ok {
		return -1
	}
	c.mu.Lock()
	if c.closed {
		c.mu.Unlock()
		return -2
	}
	c.mu.Unlock()
	c.ch <- float64(val)
	return 0
}

//export vyn_chan_send_str
func vyn_chan_send_str(chanID C.int, val *C.char) C.int {
	channels.mu.Lock()
	c, ok := channels.data[int(chanID)]
	channels.mu.Unlock()
	if !ok {
		return -1
	}
	c.mu.Lock()
	if c.closed {
		c.mu.Unlock()
		return -2
	}
	c.mu.Unlock()
	c.ch <- C.GoString(val)
	return 0
}

//export vyn_chan_recv_json
func vyn_chan_recv_json(chanID C.int, buf *C.char, bufLen C.int) C.int {
	channels.mu.Lock()
	c, ok := channels.data[int(chanID)]
	channels.mu.Unlock()
	if !ok {
		return -1
	}
	val, open := <-c.ch
	if !open {
		return -2
	}
	var s string
	switch v := val.(type) {
	case int64:
		s = fmt_int(v)
	case float64:
		s = fmt_float(v)
	case string:
		s = `"` + v + `"`
	case bool:
		if v {
			s = "true"
		} else {
			s = "false"
		}
	default:
		s = "null"
	}
	if int(bufLen) < len(s)+1 {
		return -1
	}
	dest := (*[1 << 28]byte)(unsafe.Pointer(buf))[:bufLen:bufLen]
	copy(dest, s)
	dest[len(s)] = 0
	return C.int(len(s))
}

//export vyn_chan_close
func vyn_chan_close(chanID C.int) C.int {
	channels.mu.Lock()
	c, ok := channels.data[int(chanID)]
	channels.mu.Unlock()
	if !ok {
		return -1
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.closed {
		return -2
	}
	close(c.ch)
	c.closed = true
	return 0
}

//export vyn_chan_drop
func vyn_chan_drop(chanID C.int) C.int {
	channels.mu.Lock()
	defer channels.mu.Unlock()
	if _, ok := channels.data[int(chanID)]; !ok {
		return -1
	}
	delete(channels.data, int(chanID))
	return 0
}

//export vyn_goroutine_spawn
func vyn_goroutine_spawn(fnID C.int, argJSON *C.char) C.int {
	call := goroutineCall{
		fnID:    int(fnID),
		argJSON: C.GoString(argJSON),
	}
	go func() {
		goroutineCallbacks.mu.Lock()
		goroutineCallbacks.queue = append(goroutineCallbacks.queue, call)
		goroutineCallbacks.mu.Unlock()
	}()
	return 0
}

//export vyn_goroutine_poll
func vyn_goroutine_poll(fnIDBuf *C.int, argBuf *C.char, argBufLen C.int) C.int {
	goroutineCallbacks.mu.Lock()
	defer goroutineCallbacks.mu.Unlock()
	if len(goroutineCallbacks.queue) == 0 {
		return 0
	}
	call := goroutineCallbacks.queue[0]
	goroutineCallbacks.queue = goroutineCallbacks.queue[1:]
	*fnIDBuf = C.int(call.fnID)
	s := call.argJSON
	if int(argBufLen) < len(s)+1 {
		return -1
	}
	dest := (*[1 << 28]byte)(unsafe.Pointer(argBuf))[:argBufLen:argBufLen]
	copy(dest, s)
	dest[len(s)] = 0
	return 1
}

//export vyn_select
func vyn_select(chanIDs *C.int, count C.int, buf *C.char, bufLen C.int, readyChanID *C.int) C.int {
	n := int(count)
	ids := (*[1 << 10]C.int)(unsafe.Pointer(chanIDs))[:n:n]
	cases := make([]struct {
		c  *vynChannel
		id int
	}, 0, n)
	channels.mu.Lock()
	for i := 0; i < n; i++ {
		id := int(ids[i])
		if c, ok := channels.data[id]; ok {
			cases = append(cases, struct {
				c  *vynChannel
				id int
			}{c, id})
		}
	}
	channels.mu.Unlock()
	done := make(chan struct {
		val interface{}
		id  int
	}, 1)
	for _, cs := range cases {
		go func(c *vynChannel, id int) {
			val, open := <-c.ch
			if open {
				done <- struct {
					val interface{}
					id  int
				}{val, id}
			}
		}(cs.c, cs.id)
	}
	result := <-done
	*readyChanID = C.int(result.id)
	var s string
	switch v := result.val.(type) {
	case int64:
		s = fmt_int(v)
	case float64:
		s = fmt_float(v)
	case string:
		s = `"` + v + `"`
	case bool:
		if v {
			s = "true"
		} else {
			s = "false"
		}
	default:
		s = "null"
	}
	if int(bufLen) < len(s)+1 {
		return -1
	}
	dest := (*[1 << 28]byte)(unsafe.Pointer(buf))[:bufLen:bufLen]
	copy(dest, s)
	dest[len(s)] = 0
	return C.int(len(s))
}

func fmt_int(v int64) string {
	if v == 0 {
		return "0"
	}
	neg := v < 0
	if neg {
		v = -v
	}
	buf := make([]byte, 20)
	i := len(buf)
	for v > 0 {
		i--
		buf[i] = byte('0' + v%10)
		v /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}

func fmt_float(v float64) string {
    return strconv.FormatFloat(v, 'f', -1, 64)
}

func strconv_fmt(f float64) string {
	import_strconv_once.Do(func(){})
	return strconv_format(f)
}

var import_strconv_once sync.Once

func strconv_format(f float64) string {
	b := make([]byte, 0, 32)
	b = appendFloat(b, f)
	return string(b)
}

func appendFloat(b []byte, f float64) []byte {
	if f != f {
		return append(b, "NaN"...)
	}
	if f < 0 {
		b = append(b, '-')
		f = -f
	}
	if f == 0 {
		return append(b, '0', '.', '0')
	}
	whole := int64(f)
	frac := f - float64(whole)
	b = append(b, []byte(fmt_int(whole))...)
	b = append(b, '.')
	frac *= 1e6
	fracInt := int64(frac + 0.5)
	fracStr := fmt_int(fracInt)
	for len(fracStr) < 6 {
		fracStr = "0" + fracStr
	}
	i := len(fracStr)
	for i > 1 && fracStr[i-1] == '0' {
		i--
	}
	return append(b, []byte(fracStr[:i])...)
}

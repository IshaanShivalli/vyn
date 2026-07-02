package main

import "C"
import (
	"encoding/json"
	"sync"
	"unsafe"
)

type returnSlot struct {
	values []interface{}
}

var returnStore = struct {
	mu   sync.Mutex
	data map[int]*returnSlot
	next int
}{data: make(map[int]*returnSlot)}

//export vyn_ret_new
func vyn_ret_new() C.int {
	returnStore.mu.Lock()
	defer returnStore.mu.Unlock()
	returnStore.next++
	returnStore.data[returnStore.next] = &returnSlot{}
	return C.int(returnStore.next)
}

//export vyn_ret_push_int
func vyn_ret_push_int(slotID C.int, val C.long) C.int {
	returnStore.mu.Lock()
	s, ok := returnStore.data[int(slotID)]
	returnStore.mu.Unlock()
	if !ok {
		return -1
	}
	s.values = append(s.values, int64(val))
	return C.int(len(s.values) - 1)
}

//export vyn_ret_push_float
func vyn_ret_push_float(slotID C.int, val C.double) C.int {
	returnStore.mu.Lock()
	s, ok := returnStore.data[int(slotID)]
	returnStore.mu.Unlock()
	if !ok {
		return -1
	}
	s.values = append(s.values, float64(val))
	return C.int(len(s.values) - 1)
}

//export vyn_ret_push_str
func vyn_ret_push_str(slotID C.int, val *C.char) C.int {
	returnStore.mu.Lock()
	s, ok := returnStore.data[int(slotID)]
	returnStore.mu.Unlock()
	if !ok {
		return -1
	}
	s.values = append(s.values, C.GoString(val))
	return C.int(len(s.values) - 1)
}

//export vyn_ret_push_bool
func vyn_ret_push_bool(slotID C.int, val C.int) C.int {
	returnStore.mu.Lock()
	s, ok := returnStore.data[int(slotID)]
	returnStore.mu.Unlock()
	if !ok {
		return -1
	}
	s.values = append(s.values, val != 0)
	return C.int(len(s.values) - 1)
}

//export vyn_ret_count
func vyn_ret_count(slotID C.int) C.int {
	returnStore.mu.Lock()
	s, ok := returnStore.data[int(slotID)]
	returnStore.mu.Unlock()
	if !ok {
		return -1
	}
	return C.int(len(s.values))
}

//export vyn_ret_get_json
func vyn_ret_get_json(slotID C.int, buf *C.char, bufLen C.int) C.int {
	returnStore.mu.Lock()
	s, ok := returnStore.data[int(slotID)]
	returnStore.mu.Unlock()
	if !ok {
		return -1
	}
	data, err := json.Marshal(s.values)
	if err != nil {
		return -1
	}
	if int(bufLen) < len(data)+1 {
		return -1
	}
	dest := (*[1 << 28]byte)(unsafe.Pointer(buf))[:bufLen:bufLen]
	copy(dest, data)
	dest[len(data)] = 0
	return C.int(len(data))
}

//export vyn_ret_free
func vyn_ret_free(slotID C.int) C.int {
	returnStore.mu.Lock()
	defer returnStore.mu.Unlock()
	if _, ok := returnStore.data[int(slotID)]; !ok {
		return -1
	}
	delete(returnStore.data, int(slotID))
	return 0
}
package main

import "C"
import "sync"

type deferStack struct {
	mu    sync.Mutex
	items []func()
}

var stacks = struct {
	mu   sync.Mutex
	data map[int]*deferStack
	next int
}{data: make(map[int]*deferStack)}

//export vyn_defer_new_stack
func vyn_defer_new_stack() C.int {
	stacks.mu.Lock()
	defer stacks.mu.Unlock()
	stacks.next++
	stacks.data[stacks.next] = &deferStack{}
	return C.int(stacks.next)
}

//export vyn_defer_push
func vyn_defer_push(stackID C.int, fnID C.int) C.int {
	stacks.mu.Lock()
	s, ok := stacks.data[int(stackID)]
	stacks.mu.Unlock()
	if !ok {
		return -1
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	id := int(fnID)
	s.items = append(s.items, func() {
		pendingCalls.mu.Lock()
		pendingCalls.queue = append(pendingCalls.queue, id)
		pendingCalls.mu.Unlock()
	})
	return 0
}

//export vyn_defer_run
func vyn_defer_run(stackID C.int) C.int {
	stacks.mu.Lock()
	s, ok := stacks.data[int(stackID)]
	stacks.mu.Unlock()
	if !ok {
		return -1
	}
	s.mu.Lock()
	items := make([]func(), len(s.items))
	copy(items, s.items)
	s.items = nil
	s.mu.Unlock()
	for i := len(items) - 1; i >= 0; i-- {
		items[i]()
	}
	return 0
}

//export vyn_defer_pop_call
func vyn_defer_pop_call() C.int {
	pendingCalls.mu.Lock()
	defer pendingCalls.mu.Unlock()
	if len(pendingCalls.queue) == 0 {
		return -1
	}
	id := pendingCalls.queue[0]
	pendingCalls.queue = pendingCalls.queue[1:]
	return C.int(id)
}

//export vyn_defer_drop_stack
func vyn_defer_drop_stack(stackID C.int) C.int {
	stacks.mu.Lock()
	defer stacks.mu.Unlock()
	if _, ok := stacks.data[int(stackID)]; !ok {
		return -1
	}
	delete(stacks.data, int(stackID))
	return 0
}

var pendingCalls = struct {
	mu    sync.Mutex
	queue []int
}{}
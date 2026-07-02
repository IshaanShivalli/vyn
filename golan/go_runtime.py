import threading
import queue
import json
import re
import os

_defer_stacks = {}
_defer_next_id = [0]
_defer_pending = []
_defer_lock = threading.Lock()

_return_slots = {}
_return_next_id = [0]
_return_lock = threading.Lock()

_channels = {}
_channel_next_id = [0]
_channel_lock = threading.Lock()

_goroutine_queue = []
_goroutine_lock = threading.Lock()


def vyn_defer_new_stack():
    with _defer_lock:
        _defer_next_id[0] += 1
        sid = _defer_next_id[0]
        _defer_stacks[sid] = []
        return sid


def vyn_defer_push(stack_id, fn_id):
    with _defer_lock:
        if stack_id not in _defer_stacks:
            return -1
        _defer_stacks[stack_id].append(int(fn_id))
        return 0


def vyn_defer_run(stack_id):
    with _defer_lock:
        if stack_id not in _defer_stacks:
            return -1
        items = list(_defer_stacks[stack_id])
        _defer_stacks[stack_id] = []
    for fn_id in reversed(items):
        with _defer_lock:
            _defer_pending.append(fn_id)
    return 0


def vyn_defer_pop_call():
    with _defer_lock:
        if not _defer_pending:
            return -1
        return _defer_pending.pop(0)


def vyn_defer_drop_stack(stack_id):
    with _defer_lock:
        if stack_id not in _defer_stacks:
            return -1
        del _defer_stacks[stack_id]
        return 0


def vyn_ret_new():
    with _return_lock:
        _return_next_id[0] += 1
        sid = _return_next_id[0]
        _return_slots[sid] = []
        return sid


def vyn_ret_push_int(slot_id, val):
    with _return_lock:
        if slot_id not in _return_slots:
            return -1
        _return_slots[slot_id].append(int(val))
        return len(_return_slots[slot_id]) - 1


def vyn_ret_push_float(slot_id, val):
    with _return_lock:
        if slot_id not in _return_slots:
            return -1
        _return_slots[slot_id].append(float(val))
        return len(_return_slots[slot_id]) - 1


def vyn_ret_push_str(slot_id, val):
    with _return_lock:
        if slot_id not in _return_slots:
            return -1
        _return_slots[slot_id].append(str(val))
        return len(_return_slots[slot_id]) - 1


def vyn_ret_push_bool(slot_id, val):
    with _return_lock:
        if slot_id not in _return_slots:
            return -1
        _return_slots[slot_id].append(bool(val))
        return len(_return_slots[slot_id]) - 1


def vyn_ret_count(slot_id):
    with _return_lock:
        if slot_id not in _return_slots:
            return -1
        return len(_return_slots[slot_id])


def vyn_ret_get_json(slot_id):
    with _return_lock:
        if slot_id not in _return_slots:
            return None
        return json.dumps(_return_slots[slot_id])


def vyn_ret_free(slot_id):
    with _return_lock:
        if slot_id not in _return_slots:
            return -1
        del _return_slots[slot_id]
        return 0


def vyn_ret_unpack(slot_id):
    data = vyn_ret_get_json(slot_id)
    if data is None:
        return []
    vyn_ret_free(slot_id)
    return json.loads(data)


def vyn_chan_new(buf_size=0):
    with _channel_lock:
        _channel_next_id[0] += 1
        cid = _channel_next_id[0]
        _channels[cid] = {
            'q': queue.Queue(maxsize=int(buf_size)),
            'closed': False,
            'lock': threading.Lock()
        }
        return cid


def vyn_chan_send_int(chan_id, val):
    with _channel_lock:
        c = _channels.get(chan_id)
    if c is None:
        return -1
    with c['lock']:
        if c['closed']:
            return -2
    c['q'].put(int(val))
    return 0


def vyn_chan_send_float(chan_id, val):
    with _channel_lock:
        c = _channels.get(chan_id)
    if c is None:
        return -1
    with c['lock']:
        if c['closed']:
            return -2
    c['q'].put(float(val))
    return 0


def vyn_chan_send_str(chan_id, val):
    with _channel_lock:
        c = _channels.get(chan_id)
    if c is None:
        return -1
    with c['lock']:
        if c['closed']:
            return -2
    c['q'].put(str(val))
    return 0


def vyn_chan_recv(chan_id, timeout=None):
    with _channel_lock:
        c = _channels.get(chan_id)
    if c is None:
        return None, -1
    try:
        val = c['q'].get(timeout=timeout)
        return val, 0
    except queue.Empty:
        return None, -3


def vyn_chan_recv_json(chan_id, timeout=None):
    val, status = vyn_chan_recv(chan_id, timeout=timeout)
    if status != 0:
        return None, status
    return json.dumps(val), 0


def vyn_chan_close(chan_id):
    with _channel_lock:
        c = _channels.get(chan_id)
    if c is None:
        return -1
    with c['lock']:
        if c['closed']:
            return -2
        c['closed'] = True
    return 0


def vyn_chan_drop(chan_id):
    with _channel_lock:
        if chan_id not in _channels:
            return -1
        del _channels[chan_id]
        return 0


def vyn_goroutine_spawn(fn, args=None):
    if args is None:
        args = []
    def _run():
        try:
            result = fn(*args)
            with _goroutine_lock:
                _goroutine_queue.append(('done', fn, result))
        except Exception as exc:
            with _goroutine_lock:
                _goroutine_queue.append(('error', fn, str(exc)))
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def vyn_goroutine_poll():
    with _goroutine_lock:
        if not _goroutine_queue:
            return None
        return _goroutine_queue.pop(0)


def vyn_select(chan_ids, timeout=None):
    result = queue.Queue(maxsize=1)
    threads = []

    def _try_recv(cid):
        val, status = vyn_chan_recv(cid, timeout=timeout)
        if status == 0:
            try:
                result.put_nowait((cid, val))
            except queue.Full:
                pass

    for cid in chan_ids:
        t = threading.Thread(target=_try_recv, args=(cid,), daemon=True)
        threads.append(t)
        t.start()

    try:
        cid, val = result.get(timeout=timeout)
        return cid, val
    except queue.Empty:
        return None, None
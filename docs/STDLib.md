# Vyn Standard Libraries Documentation

To use any library, import it:
```
import List
import crypto
import Stack
import math
```

Standard libs (`lib/`) are loaded as Python modules. Packages (`packages/`) are `.vyn` files. Imported modules such as `math` are exposed as module objects, so expressions like `math.sqrt(16)` work directly in Vyn code.

---

## Table of Contents

### Standard Libraries (`lib/`)
1. [String](#string)
2. [Math](#math)
3. [List](#list)
4. [Dict](#dict)
5. [Array](#array)
6. [Tuple](#tuple)
7. [Datetime](#datetime)
8. [Time](#time)
9. [OS](#os)
10. [Sys](#sys)
11. [Random](#random)
12. [JSON](#json)
13. [RE](#re)

### Security Libraries (`lib/`)
14. [crypto](#crypto)
15. [encode](#encode)
16. [uuid](#uuid)
17. [token](#token)

### Packages (`packages/`)
18. [Stack](#stack)
19. [Queue](#queue)
20. [LinkedList](#linkedlist)
21. [Deque](#deque)
22. [PriorityQueue](#priorityqueue)
23. [BinaryTree](#binarytree)
24. [Sort](#sort)
25. [Search](#search)
26. [Fibonacci](#fibonacci)
27. [Primes](#primes)
28. [StringUtils](#stringutils)
29. [Validation](#validation)
30. [Logger](#logger)

---

## String
Functions for string inspection and manipulation.
* `length(s)` — Returns the number of characters in `s`.
* `toUpperCase(s)` — Converts `s` to uppercase.
* `toLowerCase(s)` — Converts `s` to lowercase.
* `trim(s)` — Removes leading and trailing whitespace.
* `substring(s, start, end)` — Returns slice `s[start:end]`.
* `indexOf(s, search)` — First index of `search` in `s`, or `-1`.
* `lastIndexOf(s, search)` — Last index of `search` in `s`, or `-1`.
* `replace(s, find, replaceWith)` — Replaces all occurrences of `find` with `replaceWith`.
* `split(s, delimiter)` — Splits `s` by `delimiter` into a list.
* `join(*args)` — Joins arguments with spaces.
* `startsWith(s, prefix)` — Returns `true` if `s` starts with `prefix`.
* `endsWith(s, suffix)` — Returns `true` if `s` ends with `suffix`.
* `contains(s, substring)` — Returns `true` if `substring` is in `s`.
* `reverse(s)` — Reverses `s`.
* `repeat(s, count)` — Repeats `s` `count` times.
* `concat(*args)` — Concatenates all arguments.
* `format(s, *args)` — Formats `s` using `{}` placeholders.
* `padStart(s, length, char)` — Pads start of `s` with `char` to `length`.
* `padEnd(s, length, char)` — Pads end of `s` with `char` to `length`.
* `charAt(s, index)` — Character at `index`, or `""`.
* `charCodeAt(s, index)` — Unicode value at `index`, or `-1`.

---

## Math
* `pi` — Constant π ≈ 3.14159.
* `e` — Constant e ≈ 2.71828.
* `sqrt(x)` — Square root of `x`.
* `sin(x)` — Sine of `x` (radians).
* `cos(x)` — Cosine of `x` (radians).
* `tan(x)` — Tangent of `x` (radians).
* `log(x, base)` — Natural log of `x`, or log with `base`.
* `floor(x)` — Floor of `x`.
* `ceil(x)` — Ceiling of `x`.
* `pow(x, y)` — `x` to the power of `y`.
* `factorial(x)` — Factorial of `x`.
* `gcd(a, b)` — Greatest common divisor of `a` and `b`.

---

## List
* `create(*items)` — Creates a new list.
* `append(lst, item)` — Appends `item` to `lst`, returns `lst`.
* `insert(lst, index, item)` — Inserts `item` at `index`, returns `lst`.
* `remove(lst, item)` — Removes first occurrence of `item`, returns `lst`.
* `pop(lst, index=-1)` — Removes and returns item at `index`.
* `get(lst, index)` — Returns item at `index`, or `NIL`.
* `set_item(lst, index, value)` — Sets value at `index`, returns `lst`.
* `length(lst)` — Returns size of `lst`.
* `reverse(lst)` — Reverses `lst` in-place, returns `lst`.
* `sort(lst)` — Sorts `lst` in-place, returns `lst`.
* `copy(lst)` — Returns a shallow copy.
* `join(lst, separator)` — Joins elements with `separator`.
* `contains(lst, item)` — Returns `true` if `item` is in `lst`.
* `clear(lst)` — Removes all items, returns `lst`.

---

## Dict
* `create(key, val, ...)` — Creates a dict from alternating key/value pairs.
* `get(dct, key, default)` — Returns value at `key`, or `default`.
* `set_item(dct, key, value)` — Inserts/updates `key`, returns `dct`.
* `remove(dct, key)` — Deletes `key`, returns `dct`.
* `keys(dct)` — Returns list of all keys.
* `values(dct)` — Returns list of all values.
* `has_key(dct, key)` — Returns `true` if `key` exists.
* `length(dct)` — Returns number of entries.
* `clear(dct)` — Removes all entries, returns `dct`.
* `copy(dct)` — Returns a copy.

---

## Array
* `create(size, default)` — Creates a fixed-size list prefilled with `default`.
* `get(arr, index)` — Returns item at `index`, or `NIL`.
* `set_item(arr, index, value)` — Updates item at `index`, returns `arr`.
* `length(arr)` — Returns array size.
* `fill(arr, value)` — Sets all elements to `value`, returns `arr`.

---

## Tuple
* `create(*items)` — Creates an immutable tuple.
* `get(tpl, index)` — Returns item at `index`.
* `length(tpl)` — Returns tuple size.
* `to_list(tpl)` — Converts to a mutable list.
* `contains(tpl, item)` — Returns `true` if `item` is in `tpl`.
* `index_of(tpl, item)` — Returns index of `item`, or `-1`.

---

## Datetime
* `now()` — Returns current datetime as ISO string.
* `getYear()` — Current year.
* `getMonth()` — Current month.
* `getDay()` — Current day.
* `formatDate(year, month, day)` — Returns `"YYYY-MM-DD"`.
* `parseDate(dateStr)` — Parses ISO string into datetime object.
* `getCurrentTime()` — Returns current time as `"HH:MM:SS"`.
* `addDays(d, n)` — Adds `n` days to `d`, returns ISO string.
* `subtractDays(d, n)` — Subtracts `n` days from `d`, returns ISO string.
* `getTimestamp()` — Unix timestamp in milliseconds.
* `toISOString(dt)` — Formats datetime object as ISO string.

---

## Time
* `currentTimeMillis()` — Current time in milliseconds.
* `currentTimeSeconds()` — Current time in seconds.
* `sleep(milliseconds)` — Pause for `milliseconds`.
* `sleepSeconds(seconds)` — Pause for `seconds`.
* `getHour()` — Current hour.
* `getMinute()` — Current minute.
* `getSecond()` — Current second.
* `getMillisecond()` — Current millisecond.
* `formatTime(hour, minute, second)` — Returns `"HH:MM:SS"`.
* `getTimezone()` — Active timezone name.
* `addHours(t, hours)` — Adds hours to ISO time string.
* `addMinutes(t, minutes)` — Adds minutes to ISO time string.
* `addSeconds(t, seconds)` — Adds seconds to ISO time string.
* `differenceInSeconds(t1, t2)` — Seconds between `t1` and `t2`.
* `differenceInMinutes(t1, t2)` — Minutes between `t1` and `t2`.
* `differenceInHours(t1, t2)` — Hours between `t1` and `t2`.
* `isLeapSecond(second)` — Returns `true` if `second == 60`.

---

## OS
* `getcwd()` — Current working directory.
* `chdir(path)` — Change working directory.
* `listFiles(path)` — List files/folders in `path`.
* `fileExists(path)` — Returns `true` if path exists.
* `mkdir(path)` — Create directory.
* `rmdir(path)` — Delete empty directory.
* `removeFile(path)` — Delete a file.
* `copyFile(src, dest)` — Copy file.
* `renameFile(old, new)` — Rename/move file.
* `getEnv(varName)` — Get environment variable.
* `setEnv(varName, value)` — Set environment variable.
* `getHomeDir()` — User home directory.
* `getTempDir()` — System temp directory.
* `pathSeparator()` — `/` or `\` depending on OS.
* `isFile(path)` — Returns `true` if path is a file.
* `isDir(path)` — Returns `true` if path is a directory.
* `getFileSize(path)` — File size in bytes.
* `getFileModTime(path)` — File modification timestamp.

---

## Sys
* `exit(code)` — Exit interpreter with code.
* `getVersion()` — Python version string.
* `getPlatform()` — Platform identifier e.g. `win32`, `linux`.
* `getArguments()` — Command-line arguments list.
* `getEnvironment()` — All environment variables as dict.
* `getPath()` — Python path list.
* `getModules()` — Loaded module names.
* `sleep(milliseconds)` — Pause for milliseconds.
* `getTime()` — Timestamp in milliseconds.
* `executeCommand(command)` — Run shell command, return stdout.
* `getUsername()` — Current OS username.

---

## Random
* `random()` — Float in `[0.0, 1.0)`.
* `randint(a, b)` — Integer in `[a, b]` inclusive.
* `randrange(start, stop, step)` — Random element from range.
* `choice(seq)` — Random element from sequence.
* `shuffle(seq)` — Shuffle sequence in-place, return it.
* `sample(seq, k)` — `k` unique random elements from `seq`.
* `uniform(a, b)` — Float in `[a, b]`.
* `seed(s)` — Seed the random generator.

---

## JSON
* `dumps(obj, indent)` — Encode object to JSON string.
* `loads(s)` — Decode JSON string to object.
* `dump(obj, filename)` — Write JSON to file.
* `load(filename)` — Read and parse JSON from file.

---

## RE
* `match(pattern, text)` — `true` if pattern matches at start of `text`.
* `search(pattern, text)` — `true` if pattern matches anywhere in `text`.
* `isMatch(pattern, text)` — Alias of `match`.
* `findAll(pattern, text)` — List of all matches.
* `replace(pattern, replacement, text)` — Replace all matches.
* `split(pattern, text)` — Split `text` by pattern.
* `compile(pattern)` — Compile pattern to regex object.
* `escape(text)` — Escape special regex characters.
* `getGroups(pattern, text)` — Captured groups tuple, or empty tuple.
* `substitute(pattern, replacement, text)` — Alias of `replace`.

---

## crypto
Hashing and verification via `hashlib`.
* `md5(text)` — Returns MD5 hex digest of `text`.
* `sha1(text)` — Returns SHA1 hex digest of `text`.
* `sha256(text)` — Returns SHA256 hex digest of `text`.
* `sha512(text)` — Returns SHA512 hex digest of `text`.
* `verify(text, hash, algorithm)` — Returns `true` if `hash` matches `text` using `algorithm`.

```
import crypto
h = sha256("hello")
print(h)
print(verify("hello", h, "sha256"))
```

---

## encode
Base64 encoding and decoding.
* `b64encode(text)` — Base64 encode `text`.
* `b64decode(text)` — Base64 decode `text`.
* `urlsafe_encode(text)` — URL-safe base64 encode.
* `urlsafe_decode(text)` — URL-safe base64 decode.

```
import encode
enc = b64encode("hello world")
print(enc)
print(b64decode(enc))
```

---

## uuid
Unique ID generation.
* `uuidv4()` — Returns a random UUID v4 string.
* `uuidv1()` — Returns a time-based UUID v1 string.
* `isValid(uid)` — Returns `true` if `uid` is a valid UUID.

```
import uuid
id = uuidv4()
print(id)
print(isValid(id))
```

---

## token
Secure random token generation via `secrets`.
* `generateToken(nbytes)` — Hex token of `nbytes` bytes (default 32).
* `generateUrlToken(nbytes)` — URL-safe token of `nbytes` bytes.
* `generatePin(length)` — Numeric PIN of `length` digits (default 6).
* `generatePassword(length)` — Random password of `length` chars (default 16).
* `compareTokens(a, b)` — Timing-safe comparison of two tokens.

```
import token
t = generateToken(16)
print(t)
print(generatePin(4))
print(generatePassword(12))
```

---

## Stack
LIFO stack built on List. Import from packages.
* `Make()` — Create a new stack.
* `Push(stack, item)` — Push item onto stack.
* `Pop(stack)` — Remove and return top item, or `NIL` if empty.
* `Top(stack)` — Peek at top item without removing, or `NIL` if empty.
* `IsEmpty(stack)` — Returns `true` if stack is empty.
* `Size(stack)` — Returns number of items.
* `Clear(stack)` — Removes all items, returns stack.

```
import Stack
s = Make()
Push(s, 10)
Push(s, 20)
print(Top(s))
print(Pop(s))
```

---

## Queue
FIFO queue built on List. Import from packages.
* `createQ()` — Create a new queue.
* `enqueue(queue, item)` — Add item to back.
* `dequeue(queue)` — Remove and return front item, or `NIL` if empty.
* `front(queue)` — Peek at front item, or `NIL` if empty.
* `back(queue)` — Peek at back item, or `NIL` if empty.
* `isEmpty(queue)` — Returns `true` if queue is empty.
* `size(queue)` — Returns number of items.
* `clearQ(queue)` — Removes all items, returns queue.

```
import Queue
q = createQ()
enqueue(q, 1)
enqueue(q, 2)
print(front(q))
print(dequeue(q))
```

---

## LinkedList
Singly linked list built on List. Import from packages.
* `createList()` — Create a new linked list.
* `addFront(lst, item)` — Add item to front.
* `addBack(lst, item)` — Add item to back.
* `removeFront(lst)` — Remove and return front item.
* `removeBack(lst)` — Remove and return back item.
* `getNode(lst, index)` — Get item at index.
* `listSize(lst)` — Number of items.
* `listIsEmpty(lst)` — Returns `true` if empty.
* `listContains(lst, item)` — Returns `true` if item is present.
* `clearList(lst)` — Clears the list.

---

## Deque
Double-ended queue. Import from packages.
* `createDeque()` — Create a new deque.
* `pushFront(dq, item)` — Add to front.
* `pushBack(dq, item)` — Add to back.
* `popFront(dq)` — Remove and return front item.
* `popBack(dq)` — Remove and return back item.
* `peekFront(dq)` — Peek at front.
* `peekBack(dq)` — Peek at back.
* `dequeSize(dq)` — Number of items.
* `dequeIsEmpty(dq)` — Returns `true` if empty.
* `clearDeque(dq)` — Clears the deque.

---

## PriorityQueue
Min priority queue (lowest value = highest priority). Import from packages.
* `createPQ()` — Create a new priority queue.
* `pqEnqueue(pq, item)` — Add item in sorted order.
* `pqDequeue(pq)` — Remove and return highest priority item.
* `pqPeek(pq)` — Peek at highest priority item.
* `pqSize(pq)` — Number of items.
* `pqIsEmpty(pq)` — Returns `true` if empty.
* `clearPQ(pq)` — Clears the queue.

---

## BinaryTree
Binary search tree using list nodes. Import from packages.
* `createTree()` — Create a new tree.
* `makeNode(value)` — Create a node with `[value, -1, -1]`.
* `treeInsert(tree, value)` — Insert a new node.
* `treeSize(tree)` — Number of nodes.
* `treeIsEmpty(tree)` — Returns `true` if empty.
* `treeGet(tree, index)` — Get node at index.

---

## Sort
Sorting algorithms. Import from packages.
* `bubbleSort(lst)` — Bubble sort, returns sorted `lst`.
* `selectionSort(lst)` — Selection sort, returns sorted `lst`.
* `insertionSort(lst)` — Insertion sort, returns sorted `lst`.

```
import Sort
import List
lst = create(5, 3, 8, 1)
print(bubbleSort(lst))
```

---

## Search
Search algorithms. Import from packages.
* `linearSearch(lst, target)` — Returns index of `target`, or `-1`.
* `binarySearch(lst, target)` — Binary search on sorted list, returns index or `-1`.

---

## Fibonacci
Fibonacci utilities. Import from packages.
* `fibRecursive(n)` — Recursive Fibonacci of `n`.
* `fibIterative(n)` — Iterative Fibonacci of `n`.
* `fibSequence(n)` — List of Fibonacci numbers from 0 to `n`.

---

## Primes
Prime number utilities. Import from packages.
* `isPrime(n)` — Returns `true` if `n` is prime.
* `getPrimes(limit)` — List of all primes up to `limit`.
* `nextPrime(n)` — Next prime after `n`.

---

## StringUtils
Extra string helpers. Import from packages.
* `countOccurrences(str, sub)` — Count occurrences of `sub` in `str`.
* `isPalindrome(str)` — Returns `true` if `str` is a palindrome.
* `capitalize(str)` — Capitalizes first letter, lowercases rest.
* `isBlank(str)` — Returns `true` if `str` is empty or whitespace.

---

## Validation
Input validation helpers. Import from packages.
* `isNil(val)` — Returns `true` if `val` is `NIL`.
* `isPositive(n)` — Returns `true` if `n > 0`.
* `isNegative(n)` — Returns `true` if `n < 0`.
* `isZero(n)` — Returns `true` if `n == 0`.
* `inRange(n, low, high)` — Returns `true` if `low <= n <= high`.
* `isNonEmpty(str)` — Returns `true` if `str` is not blank.
* `hasMinLength(str, min)` — Returns `true` if `length(str) >= min`.
* `hasMaxLength(str, max)` — Returns `true` if `length(str) <= max`.

---

## Logger
Levelled print logger. Import from packages.
* `logInfo(message)` — Prints `[INFO] message`.
* `logWarn(message)` — Prints `[WARN] message`.
* `logError(message)` — Prints `[ERROR] message`.
* `logDebug(message)` — Prints `[DEBUG] message`.
* `log(level, message)` — Prints `[level] message`.

```
import Logger
logInfo("Server started")
logWarn("Low memory")
logError("Connection failed")
```
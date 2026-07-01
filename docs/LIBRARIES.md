# Vyn Standard Libraries Documentation

This document describes all standard libraries available in Vyn. To use any of these libraries, load them via the `import` command:
```vyn
import math
import lib/String
```

Once imported, library functions and modules are available in the current scope. The standard `math` module is exposed as a module object, so `math.sqrt(16)` works directly in Vyn code.

---

## Table of Contents
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
13. [RE (Regular Expressions)](#re-regular-expressions)

---

## String
Functions for string inspection and manipulation.
* `length(s)`: Returns the number of characters in `s`.
* `toUpperCase(s)`: Converts `s` to uppercase.
* `toLowerCase(s)`: Converts `s` to lowercase.
* `trim(s)`: Removes leading and trailing whitespace.
* `substring(s, start, end=nil)`: Returns a substring starting at index `start` up to (but not including) index `end`. If `end` is omitted, goes to the end of the string.
* `indexOf(s, search, start=0)`: Finds the first occurrence of `search` starting at index `start`. Returns `-1` if not found.
* `lastIndexOf(s, search, start=nil)`: Finds the last occurrence of `search` searching backwards.
* `replace(s, find, replaceWith)`: Replaces occurrences of `find` in `s` with `replaceWith`.
* `split(s, delimiter=nil)`: Splits `s` by `delimiter` into a list. If `delimiter` is omitted, returns `[s]`.
* `join(*args)`: Joins multiple arguments with spaces.
* `startsWith(s, prefix)`: Returns `true` if `s` starts with `prefix`.
* `endsWith(s, suffix)`: Returns `true` if `s` ends with `suffix`.
* `contains(s, substring)`: Returns `true` if `substring` is found in `s`.
* `reverse(s)`: Reverses `s`.
* `repeat(s, count)`: Repeats `s` `count` times.
* `concat(*args)`: Concatenates all arguments into a single string.
* `format(s, *args)`: Formats `s` using Python-style `.format()` placeholders `{}`.
* `padStart(s, length, char=" ")`: Pads the beginning of `s` with `char` until it reaches `length`.
* `padEnd(s, length, char=" ")`: Pads the end of `s` with `char` until it reaches `length`.
* `charAt(s, index)`: Returns the character at index `index` or `""` if out of bounds.
* `charCodeAt(s, index)`: Returns the Unicode integer value of the character at `index` or `-1` if out of bounds.

---

## Math
Constants and mathematical operations.
* `pi`: Constant $\pi \approx 3.14159$.
* `e`: Constant $e \approx 2.71828$.
* `sqrt(x)`: Returns the square root of `x`.
* `sin(x)`: Returns the sine of `x` (in radians).
* `cos(x)`: Returns the cosine of `x` (in radians).
* `tan(x)`: Returns the tangent of `x` (in radians).
* `log(x, base=nil)`: Returns the natural logarithm of `x`, or logarithm with specified `base`.
* `floor(x)`: Returns the largest integer less than or equal to `x`.
* `ceil(x)`: Returns the smallest integer greater than or equal to `x`.
* `pow(x, y)`: Returns $x^y$.
* `factorial(x)`: Returns the factorial of integer `x`.
* `gcd(a, b)`: Returns the greatest common divisor of `a` and `b`.

---

## List
Functions for working with dynamic arrays/lists.
* `create(*items)`: Creates a new list containing the arguments.
* `append(lst, item)`: Appends `item` to the end of `lst` and returns `lst`.
* `insert(lst, index, item)`: Inserts `item` at `index` in `lst` and returns `lst`.
* `remove(lst, item)`: Removes the first occurrence of `item` from `lst` and returns `lst`.
* `pop(lst, index=-1)`: Removes and returns the item at `index` (defaults to the last item). Returns `nil` on out of bounds.
* `get(lst, index)`: Returns the item at `index`. Returns `nil` on out of bounds.
* `set_item(lst, index, value)`: Sets the value at `index` to `value`.
* `length(lst)`: Returns the size of `lst`.
* `reverse(lst)`: Reverses `lst` in-place and returns it.
* `sort(lst)`: Sorts `lst` in-place and returns it.
* `copy(lst)`: Returns a shallow copy of `lst`.
* `join(lst, separator="")`: Joins elements of `lst` with `separator`.
* `contains(lst, item)`: Returns `true` if `item` is present in `lst`.
* `clear(lst)`: Removes all items from `lst`.

---

## Dict
Functions for managing key-value maps.
* `create(**kwargs)`: Creates a dictionary with given key-value pairs (e.g. `create(name="Alice", age=20)`).
* `get(dct, key, default=nil)`: Returns value at `key`, or `default` if the key doesn't exist.
* `set_item(dct, key, value)`: Inserts/updates `key` with `value`.
* `remove(dct, key)`: Deletes `key` from `dct`.
* `keys(dct)`: Returns a list of all keys in `dct`.
* `values(dct)`: Returns a list of all values in `dct`.
* `has_key(dct, key)`: Returns `true` if `key` exists in `dct`.
* `length(dct)`: Returns the size of `dct`.
* `clear(dct)`: Removes all entries.
* `copy(dct)`: Returns a copy of `dct`.

---

## Array
Fixed-size array wrappers.
* `create(size, default=nil)`: Creates a list of length `size` prefilled with `default`.
* `get(arr, index)`: Returns item at `index` or `nil` if out of bounds.
* `set_item(arr, index, value)`: Updates item at `index`.
* `length(arr)`: Returns the array size.
* `fill(arr, value)`: Sets all elements of `arr` to `value`.

---

## Tuple
Immutable sequence operations.
* `create(*items)`: Creates an immutable tuple.
* `get(tpl, index)`: Returns item at `index`.
* `length(tpl)`: Returns tuple size.
* `to_list(tpl)`: Converts tuple to a mutable list.
* `contains(tpl, item)`: Returns `true` if `item` is in `tpl`.
* `index_of(tpl, item)`: Returns the index of `item`, or `-1` if not found.

---

## Datetime
High-level date and time manipulations.
* `now()`: Returns a Python `datetime` object representing the current date and time.
* `getYear()`: Returns current year.
* `getMonth()`: Returns current month.
* `getDay()`: Returns current day of the month.
* `formatDate(year, month, day)`: Formats date as `"YYYY-MM-DD"`.
* `parseDate(dateStr)`: Parses an ISO format string into a `datetime` object.
* `getCurrentTime()`: Returns current time object.
* `addDays(d, n)`: Adds `n` days to datetime `d` (ISO string or object).
* `subtractDays(d, n)`: Subtracts `n` days.
* `getTimestamp()`: Returns current UNIX timestamp in milliseconds.
* `toISOString(dt)`: Formats `dt` object into an ISO string.

---

## Time
Helpers for timeouts and time arithmetic.
* `currentTimeMillis()`: Returns current time in milliseconds.
* `currentTimeSeconds()`: Returns current time in seconds.
* `sleep(milliseconds)`: Suspends execution for `milliseconds`.
* `sleepSeconds(seconds)`: Suspends execution for `seconds`.
* `getHour()`: Returns current hour.
* `getMinute()`: Returns current minute.
* `getSecond()`: Returns current second.
* `getMillisecond()`: Returns current millisecond.
* `formatTime(hour, minute, second)`: Formats time as `"HH:MM:SS"`.
* `getTimezone()`: Returns active timezone name.
* `addHours(t, hours)`: Adds hours to ISO time string `t`.
* `addMinutes(t, minutes)`: Adds minutes to ISO time string `t`.
* `addSeconds(t, seconds)`: Adds seconds to ISO time string `t`.
* `differenceInSeconds(time1, time2)`: Returns difference in seconds between two times.
* `differenceInMinutes(time1, time2)`: Returns difference in minutes.
* `differenceInHours(time1, time2)`: Returns difference in hours.
* `isLeapSecond(second)`: Returns `true` if `second` is `60`.

---

## OS
Operating system file management and system variables.
* `getcwd()`: Returns the current working directory path.
* `chdir(path)`: Changes the current working directory.
* `listFiles(path)`: Lists all files/folders in `path`.
* `fileExists(path)`: Returns `true` if the path exists.
* `mkdir(path)`: Creates a new directory.
* `rmdir(path)`: Deletes an empty directory.
* `removeFile(path)`: Deletes a file.
* `copyFile(src, dest)`: Copies a file from `src` to `dest`.
* `renameFile(oldName, newName)`: Renames/moves a file.
* `getEnv(varName)`: Gets environment variable value.
* `setEnv(varName, value)`: Sets environment variable value.
* `getHomeDir()`: Returns user's home directory.
* `getTempDir()`: Returns system temporary directory.
* `pathSeparator()`: Returns active path separator (`/` or `\`).
* `isFile(path)`: Returns `true` if `path` is a file.
* `isDir(path)`: Returns `true` if `path` is a directory.
* `getFileSize(path)`: Returns file size in bytes.
* `getFileModTime(path)`: Returns file modification timestamp.

---

## Sys
Interpreter controls and environment queries.
* `exit(code=0)`: Terminates interpreter with `code`.
* `getVersion()`: Returns Python version string.
* `getPlatform()`: Returns platform identifier (e.g. `'win32'`).
* `getArguments()`: Returns list of command-line arguments.
* `getEnvironment()`: Returns dictionary of environment variables.
* `getPath()`: Returns Python path list.
* `getModules()`: Returns list of imported modules.
* `sleep(milliseconds)`: Sleeps for milliseconds.
* `getTime()`: Returns timestamp in milliseconds.
* `executeCommand(command)`: Executes system command and returns stdout.
* `getUsername()`: Returns active username.

---

## Random
Random number generation utilities.
* `random()`: Returns random float in the range $[0.0, 1.0)$.
* `randint(a, b)`: Returns random integer in range $[a, b]$ (inclusive).
* `randrange(start, stop=nil, step=1)`: Returns a randomly selected element from `range(start, stop, step)`.
* `choice(seq)`: Returns a random element from non-empty sequence `seq`.
* `shuffle(seq)`: Shuffles sequence `seq` in-place and returns it.
* `sample(seq, k)`: Returns a list of `k` unique elements chosen from `seq`.
* `uniform(a, b)`: Returns random float in range $[a, b]$.
* `seed(s=nil)`: Seeds the random number generator.

---

## JSON
Serialization to and from JSON format.
* `dumps(obj, indent=nil)`: Encodes Python object `obj` into a JSON string.
* `loads(s)`: Decodes JSON string `s` into Python objects.
* `dump(obj, filename)`: Writes `obj` to file `filename` as JSON.
* `load(filename)`: Reads and parses JSON from `filename`.

---

## RE (Regular Expressions)
Regular expression matching and replacements.
* `match(pattern, text)`: Returns `true` if `pattern` matches at the start of `text`.
* `search(pattern, text)`: Returns `true` if `pattern` matches anywhere in `text`.
* `isMatch(pattern, text)`: Alias of `match`.
* `findAll(pattern, text)`: Returns list of all matches.
* `replace(pattern, replacement, text)`: Replaces matches of `pattern` with `replacement` in `text`.
* `split(pattern, text)`: Splits `text` by occurrences of `pattern`.
* `compile(pattern)`: Compiles pattern into a regex object.
* `escape(text)`: Escapes special regex characters in `text`.
* `getGroups(pattern, text)`: Returns tuple of captured groups if match found, else empty tuple.
* `substitute(pattern, replacement, text)`: Alias of `replace`.

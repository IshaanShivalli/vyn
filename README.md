# Vyn Programming Language

Vyn is a lightweight, dynamically-typed scripting language with an interactive REPL and support for structured programming. Vyn source files use the `.vyn` extension.

![Build](https://github.com/IshaanShivalli/vyn/actions/workflows/build.yml/badge.svg)
![License](https://img.shields.io/github/license/IshaanShivalli/vyn)
![Stars](https://img.shields.io/github/stars/IshaanShivalli/vyn)

---

## Getting Started

To get started with Vyn, you'll need to have Python 3.6 or later installed. You can then clone the Vyn repository from GitHub and run the `main.py` file to start the interactive REPL.

```powershell
git clone https://github.com/IshaanShivalli/vyn.git
cd vyn
python main.py
```

## Running Vyn Code

### Interactive REPL
To start the interactive shell, run the `main.py` entry point:
```powershell
python main.py
```
This opens the REPL prompt:
```
>>> 
```

### Running `.vyn` Files
To execute a source file (e.g., `script.vyn`), use the `DOF` (Do File) command in the REPL:
```
>>> DOF("script.vyn")
```
Or use the `import` statement to load and run another module:
```vyn
import script
```

---

## Language Reference & Syntax

### Comments
Comments begin with the `#` symbol and continue to the end of the line:
```vyn
# This is a comment
x = 5  # Assigning a value
```

### Data Types
Vyn supports:
* **Integers & Floats:** `42`, `3.14`
* **Booleans:** `true` and `false` (lowercase)
* **Strings:** `"hello"` or `'world'`
* **NIL:** Represents the absence of a value (`nil` or `NIL`)

---

### Variables & Assignment
Variables are declared dynamically when assigned:
```vyn
x = 10
name = "Alice"
y = x + 5
```

#### User Input (`IN`)
Read typed input directly into variables using `IN(type "prompt")`:
```vyn
age = IN(int "Enter age: ")
weight = IN(float "Enter weight: ")
name = IN(str "Your name: ")
active = IN(bool "Active? ")  # Accepts: true/false, t/f, yes/no, y/n, 1/0
```

---

### Operators & Expressions

#### Arithmetic
Operators include `+` (addition), `-` (subtraction), `*` (multiplication), `/` (division), `%` (modulo), and `**` (exponentiation):
```vyn
result = 5 + 3 * 2 ** 3  # Follows standard operator precedence
```

#### String Concatenation
Vyn provides two ways to concatenate strings:
1. **Arithmetic Precedence (`++`):** Concatenates strings with a lower precedence than addition, meaning math operations are grouped first. **(Recommended)**
   ```vyn
   print("Result: " ++ 1 + 1)
   # Output: Result: 2
   ```
2. **Standard Concatenation (`+`):** Concatenates if either operand is a string, but has the same precedence as addition.
   ```vyn
   print("Result: " + 1 + 1)
   # Output: Result: 11
   ```

#### Comparisons
Supports standard relational operators: `<`, `>`, `<=`, `>=`, `==`, `!=`:
```vyn
is_greater = x > 5
is_equal = name == "Alice"
```

#### Boolean Logic
Logical operations use `and`, `or`, and `not`:
```vyn
can_proceed = true and not false
```

#### Ternary Operator
Inline conditional expression: `condition ? true_part : false_part`
```vyn
status = age >= 18 ? "adult" : "minor"
```

---

### Conditionals (`IF / Elif / Else`)
Vyn supports block conditionals. Conditions must be wrapped in parentheses `()` or curly braces `{}` and end with `do`. The block is closed with `end`.

```vyn
IF ( x > 10 ) do
  print("x is large")
Elif { x == 10 } do
  print("x is exactly 10")
Else do
  print("x is small")
end
```

---

### Loops (`forLoop / whileLoop`)
Vyn supports loops with full control flow propagation (`break` and `continue`).

#### For Loop
Executes with an initialization, condition, and step expression separated by semicolons:
```vyn
forLoop { i = 1; i <= 5; i: i + 1 } do
  print("Iteration:", i)
endLoop
```

#### While Loop
Runs as long as the condition remains true:
```vyn
count = 1
whileLoop { count <= 5 } do
  print("Count:", count)
  count = count + 1
endLoop
```

---

### Functions
Functions are first-class values in Vyn. They can be named or declared anonymously and assigned to variables. Closed with `endFunc`.

#### Definition
```vyn
# Named function
function add(a, b) perform
  return a + b
endFunc

# Anonymous function assigned to a variable
multiply = function(x, y) perform
  return x * y
endFunc
```

#### Return Statements
Functions return values using `return`. Returning from nested conditionals or loops is fully supported:
```vyn
function checkNumber(val) perform
  IF ( val > 0 ) do
    return "Positive"
  end
  return "Non-positive"
endFunc
```

---

### Object Oriented Programming (`Class`)
Vyn supports simple classes. A class is closed with `endClass`, and calling the class creates an object.

```vyn
Class obj Person(name, age) have
  function greet() perform
    return "Hello " ++ name
  endFunc

  function birthday() perform
    this.age = this.age + 1
    return this.age
  endFunc
endClass

p = Person("Alice", 20)
print(p.name)
print(p.greet())
print(p.birthday())
```

`Class Person(...) have` is also accepted. Constructor parameters become object fields, methods can read them directly, and methods can update fields with `this.field = value`.

---

### Structured Data (`struct` / `union`)
Vyn supports lightweight structs and unions for grouping related data.

#### Structs
```vyn
import math

struct Point {
  x: int
  y: int
  method distFromOrigin() {
    return math.sqrt(this.x * this.x + this.y * this.y)
  }
}

p = Point()
p.x = 3
p.y = 4
print(p.distFromOrigin())
```

#### Unions
```vyn
union Number {
  i: int
  f: float
}

u = Number()
u.i = 7
u.f = 2.5
print(u.i)
print(u.f)
```

Imported modules such as `math` are exposed as module objects, so `math.sqrt(9)` works directly in Vyn code.

---

### Database Integration
Vyn registers the database runtime globally at startup. SQLite works out of the box; MySQL and Postgres use optional Python drivers.

#### Native DB Syntax
```vyn
DB_OPEN "sqlite" "app.sqlite" AS conn
DB_EXECUTE conn "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
DB_EXECUTE conn "INSERT INTO users (name) VALUES ('Ada')"
DB_QUERY conn "SELECT name FROM users" AS rows
print(rows)
DB_CLOSE conn
```

#### Function Syntax
```vyn
conn = connect("sqlite", "app.sqlite")
db.execute(conn, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
db.execute(conn, "INSERT INTO users (name) VALUES ('Ada')")
rows = db.query(conn, "SELECT name FROM users")
print(rows)
db.close(conn)
```

Available helpers include `connectSqlite`, `connectMysql`, `connectPostgres`, `dbQuery`, `dbExecute`, `dbClose`, `db_query`, `db_execute`, `db_close`, and the `db` namespace.

---

### Built-in Standard Libraries

## Examples

### Basics

```vyn
# Variables and basic expressions.
name = "Vyn"
version = 1
score = 7 + 3 * 2
power = 2 ** 5
remainder = 17 % 5
message = "Hello " ++ name
status = score >= 10 ? "ready" : "waiting"
items = [1, 2, 3]
profile = {"name": "Ishaan", "level": 5}

print("message:", message)
print("score:", score)
print("power:", power)
print("remainder:", remainder)
print("status:", status)
print("first item:", items[0])
print("profile level:", profile["level"])
print("typeof score:", typeof(score))
print("typeof items:", typeof(items))
```

### Conditionals

```vyn
# IF / Elif / Else blocks.
temperature = 29

IF ( temperature > 35 ) do
  print("hot")
Elif { temperature >= 25 } do
  print("warm")
Else do
  print("cool")
end

age = 16
category = age >= 18 ? "adult" : "minor"
print("category:", category)
```

### Loops

```vyn
# forLoop, whileLoop, repeatUntil, forIn, break, and continue.
total = 0
forLoop { i = 1; i <= 5; i: i + 1 } do
  total = total + i
endLoop
print("sum 1..5:", total)

count = 0
whileLoop { count < 3 } do
  count++
  print("while count:", count)
endLoop

hits = 0
repeatUntil { hits == 2 } do
  hits++
  print("repeat hit:", hits)
endLoop

forIn { item in [10, 20, 30] } do
  print("forIn item:", item)
endLoop

forLoop { n = 1; n <= 3; n: n + 1 } do
  print("continue loop before:", n)
  continue
  print("continue loop after:", n)
endLoop

forLoop { stopAt = 1; stopAt <= 3; stopAt: stopAt + 1 } do
  print("break loop before:", stopAt)
  break
  print("break loop after:", stopAt)
endLoop
```

### Functions

```vyn
# Named functions, assigned functions, defaults, lambdas, and nested returns.
function add(a, b) perform
  return a + b
endFunc

multiply = function(a, b) perform
  return a * b
endFunc

function greet(name, greeting = "Hello") perform
  return greeting ++ " " ++ name
endFunc

function sign(value) perform
  IF ( value > 0 ) do
    return "positive"
  Elif { value == 0 } do
    return "zero"
  Else do
    return "negative"
  end
endFunc

double = lambda x: x * 2

print("add:", add(2, 3))
print("multiply:", multiply(4, 5))
print(greet("Vyn"))
print(greet("Vyn", "Hi"))
print("sign:", sign(-4))
print("double:", double(9))
```

## Language Reference

### Variables & Assignment
- `x = 10` - integer
- `name = "John"` - string
- `value = IN(int "Prompt: ")` - input

### Arithmetic & Expressions
- `result = 5 + 3 * 2` - operators: +, -, *, /, %, **
- `x = 10 ? "yes" : "no"` - ternary operator

### Comparisons
- `x > 5, x < 10, x == 5, x != 0, x >= 5, x <= 5`

### Boolean & Logic
- `result = true and false, true or false, not true`

### Print
- `print(x)` - single value
- `print(x, y, z)` - multiple values
- `print("hello " + name)` - string concatenation

### Input
- `age = IN(int "Enter age: ")` - read integer
- `name = IN(str "Your name: ")` - read string
- `active = IN(bool "Active? ")` - read boolean

### Functions
- `myFunc = function(x, y) perform` - define function
- `myFunc(3, 5)` - call function

### Conditionals
- `IF ( x > 5 ) do`
- `Elif { x == 5 } do`
- `Else do`
- `end`

### Loops
- `forLoop { i = 1; i < 10; i: i + 1 } do`
- `whileLoop { count < 10 } do`

### Imports
- `import myfile` - load and execute myfile.vyn






#### File I/O Functions
The following actions are registered globally:
* `open_file(path, mode)` — Opens file handle
* `read_file(handle, size)` — Reads contents
* `read_line(handle)` — Reads a single line
* `write_file(handle, data)` — Writes text to file
* `close_file(handle)` — Closes file handle
* `list_dir(path)` — Lists directory files
* `exists(path)` — Checks if path exists

#### Modules (e.g., `String`)
Import external utilities from the `lib/` directory using the `import` command. For example, to load the standard String manipulations:
```vyn
import lib/String

# Now you can use loaded functions:
trimmed = trim("  hello  ")
upper = toUpperCase("vyn")
```
Available modules inside the `lib/` directory include:
* **`String.py`**: Exports `length`, `toUpperCase`, `toLowerCase`, `trim`, `substring`, `indexOf`, `lastIndexOf`, `replace`, `split`, `join`, `startsWith`, `endsWith`, `contains`, `reverse`, `repeat`, `concat`, `format`, `padUnused`, etc.
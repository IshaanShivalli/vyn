# Vyn Programming Language

Vyn is a lightweight, dynamically-typed scripting language with an interactive REPL and support for structured programming. Vyn source files use the `.vyn` extension.

![Build](https://github.com/IshaanShivalli/vyn/actions/workflows/build.yml/badge.svg)
![License](https://img.shields.io/github/license/IshaanShivalli/vyn)
![Stars](https://img.shields.io/github/stars/IshaanShivalli/vyn)

---

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

### Built-in Standard Libraries

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

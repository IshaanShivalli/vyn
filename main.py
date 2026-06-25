import error
import loops
import conditionals
import variables
from functions import start

if __name__ == '__main__':
    start()

# ENTRY POINT & LANGUAGE REFERENCE: Initializes interpreter and provides complete syntax guide
#
# VARIABLES & ASSIGNMENT:
# x = 10                                    - integer
# name = "John"                             - string
# value = IN(int "Prompt: ")               - input
#
# ARITHMETIC & EXPRESSIONS:
# result = 5 + 3 * 2                       - operators: +, -, *, /, %, **
# x = 10 ? "yes" : "no"                    - ternary operator
#
# COMPARISONS:
# x > 5, x < 10, x == 5, x != 0, x >= 5, x <= 5
#
# BOOLEAN & LOGIC:
# result = true and false, true or false, not true
#
# PRINT:
# print(x)                                  - single value
# print(x, y, z)                            - multiple values
# print("hello " + name)                    - string concatenation
#
# INPUT:
# age = IN(int "Enter age: ")              - read integer
# name = IN(str "Your name: ")             - read string
# active = IN(bool "Active? ")             - read boolean
#
# FUNCTIONS:
# myFunc = function(x, y) perform          - define function
#   sum = x + y
#   return sum
# endFunc
# myFunc(3, 5)                             - call function
#
# CONDITIONALS:
# IF ( x > 5 ) do
#   print("greater")
# Elif { x == 5 } do
#   print("equal")
# Else do
#   print("less")
# end
#
# LOOPS:
# forLoop { i = 1; i < 10; i: i + 1 } do
#   print(i)
# endLoop
#
# whileLoop { count < 10 } do
#   count = count + 1
# endLoop
#
# IMPORTS:
# import myfile                             - load and execute myfile.vyn

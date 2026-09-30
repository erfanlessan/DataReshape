# Extracting header cells
***
## Relevant lines of code
```python
    with open(template_file, "r", newline="") as f:
        header_lines = [next(f) for _ in range(HEADER_LINE_COUNT)
```
## Return a file handle
The line:
```python
 with open(template_file, "r", newline="") as f:
```
### Use of with open(..., ..., ...)
Returns a file handle that you are able to use in the indentation that follows. At the end of that block, the file closes. This practice makes the process of grabbing and disposing of the file handle safer.

## Use a list comprehension to get 
### Relevant code
```python
    with open(template_file, "r", newline="") as f:
        header_lines = [next(f) for _ in range(HEADER_LINE_COUNT)]
```
### Meaning of `_` 
The underscore `_` character is a placeholder variable name. 

### Use of a list comprehension
Instead of writing:
```python
squares = []

for x in range(5):

    squares.append(x * x)

```
You may write:
```python
squares = [x * x for x in range(5)]
```
### next() function
The function `next(f)` returns the next line of text from the files. For instance, say your target_format.csv contains:
```
File name,Example
Title comment,
Trigger Time,
Ch,
Mode,
Range,
Comment,
Scaling,
Ratio,
Offset,
Time,CH1,CH2
0.0,1.2,3.4
0.1,1.3,3.5
```
The **file pointer**[^1], starts from the first line `File name,Example`. If you read one line, python returns:
```
File name,Example
```
And then moves the pointer to the next line. 
```
Title comment,
```

[^1]: This is simply the file object's record of where the next read or write operation will happen.
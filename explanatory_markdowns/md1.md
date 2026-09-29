# Prompting mechanism
***
## Relevant lines of code
```python
if __name__ == "__main__":
    main()
```
## What does 'name' do?
Every python module gets a `__name__` value. When Spyder runs the file as a script, Python sets:
```python
__name__ = "__main__"
```
Therefore, when the execution reaches:
```python
if __name__ = "__main__":
    main()
```

## Why is `main()` right at the bottom?
The program has the following structure:
1. Imports (csv and os libraries)
2. Determine script directory
3. Header line count, make a column map, identify time source column. Setup placeholder rows.
4. Function definitions
    1. def reshape_csv()
    2. def main()
5. If statement, check whether `__name__` is equal to `__main__`. If so, run the function main(), which also runs reshape_csv().



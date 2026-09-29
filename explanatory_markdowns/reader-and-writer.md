# Reader and writer
***
## csv.DictReader
This method creates an object that knows how to work with CSV files. This method assumes that the firsts row that your method sees contain the column names. 
### What to do if first rows aren't column names
You may simply interate the file pointer as follows:
```python
# Iterate file pointer for non-column name rows
for _ in range(4):
    next(infile)

# Afrer incrementing file pointer, then read file
reader = csv.DictReader(infile)

```
A useful way to think about it is:
```python
next(infile)
```
means:
> "Read one line and move the file pointer to the next line."

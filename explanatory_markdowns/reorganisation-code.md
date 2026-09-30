## row in reader
```
for row in reader:
```
This is a loop that repeadedly asks reader for the next row from the CSV file. Each iteration returns a new dictionary corresponding to one data row.

### reader as an iterator
reader is an iterator that produces dictionaries, one for each data row in the CSV. For example, if the input CSV is: 
```
TimeFromRecordStart_s,CH1_1,CH1_2
0.0,25.2,25.18
0.1,25.23,25.12
```
The first reader iterator will produce:
```
{
    "TimeFromRecordStart\_s": "0.0",
    "CH1_1": "25.2",
    "CH1_2": "25.18"
}

```
And then the second reader iterator will produce:
```
{
    "TimeFromRecordStart\_s": "0.1",
    "CH1\_1": "25.23",
    "CH1\_2": "25.12"
}

```

## Populating row by row
### Relevant code
```python
            data_row = [row[TIME_SOURCE_COLUMN]]
            data_row += [row[source_col] for source_col in COLUMN_MAP.values()]
            data_row += ALARM_PLACEHOLDER
            data_row += ALARM_SOURCE_PLACEHOLDER
            data_row.append(EVENT_PLACEHOLDER)
            data_row.append("")  # trailing empty field, matching the template
```
Here, you are roughly building the following row vector[^1]

$$
\begin{bmatrix}
\mathrm{TIME\_SOURCE\_COLUMN(row)} & \mathrm{\vec{V}_{CE}^T (row)} & \mathrm{\vec{T}_{c}^T(row)} & \mathrm{ALARM\_SOURCE\_PLACEHOLDER(row)} & \mathrm{EVENT\_PLACEHOLDER(row)}
\end{bmatrix}
$$
## Process of reorganising data
When python executes `COLUMN\_MAP.values()`, we get:
```
[
    "CH2_1_UU_V",
    "CH2_2_UL_V",
    "CH2_3_VU_V"
]

```
This executes a list comprehension returning the row data in the order specified by COLUMN_MAP.values().


[^1]: This is just a conceptual representation and may not have the columns in the exact order
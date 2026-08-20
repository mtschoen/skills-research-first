# orderflow

A small Python library for processing customer orders and generating
daily sales reports.

## Features

- Parse raw order lines into validated orders
- Compute order totals with tax, shipping, and volume discounts
- Track inventory stock levels and flag low-stock items
- Generate daily summary reports
- Send alerts for low stock and completed reports

## Usage

```python
from orderflow.orders import handle_order_input

receipt = handle_order_input("CUST-001,widget,3,9.99,no")
print(receipt)
```

Run the demo:

```
python -m orderflow.main
```

## Running tests

```
python -m unittest discover -s tests -t .
```

or, if pytest is installed:

```
python -m pytest
```

# Beancount Analysis

Analyze beancount files.

> **Note**: WIP

Currently it's simply visualization of the following query:

```sql
SELECT 
    account, convert(sum(cost(position)), 'CNY') as total, year, month
WHERE
    account ~ "Expenses:*" OR account ~ "Income:*"
GROUP BY year, month, account 
ORDER BY total, account DESC
```

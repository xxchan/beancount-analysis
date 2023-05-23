# %%
import pandas as pd
from beancount.loader import load_string
from beancount.query import query
from utils import *
import streamlit as st
import plotly.express as px

beancounts = []


uploaded_file = st.file_uploader(
    "please upload your beancount files", type=["beancount"], accept_multiple_files=True
)
if uploaded_file is not None and len(uploaded_file) > 0:
    for i in range(len(uploaded_file)):
        beancounts.append(uploaded_file[i].read().decode("utf-8"))
else:
    st.stop()

entries, errors, options = load_string("\n".join(beancounts))

# run the query
query_string = """
SELECT 
    account, convert(sum(cost(position)), 'CNY') as total,year, month
WHERE
    account ~ "Expenses:*" OR account ~ "Income:*"
GROUP BY year, month, account 
ORDER BY total, account DESC
"""

types, rows = query.run_query(entries, options, query_string, numberify=True)

data = to_csv(types, rows)


# %%
from decimal import Decimal

df = pd.read_csv(
    data,
)
pd.set_option("display.float_format", "{:.2f}".format)

# display(df)

df = df.pivot(index="account", values="total (CNY)", columns=["year", "month"]).fillna(
    0
)
# sort columns
df = df.reindex(sorted(df.columns), axis=1)

st.write("## Monthly Summary of Expenses and Income")
st.dataframe(df, use_container_width=True)


def agg(kind):
    st.write(f"### Total {kind} for each month")
    col1, col2 = st.columns(2)
    agg = df[df.index.str.contains(kind)].sum(axis=0)
    # reset index (year, month) to one column "month"
    agg = agg.reset_index(name="total")
    agg["month"] = agg["year"].astype(str) + "-" + agg["month"].astype(str)
    agg = agg.drop(columns=["year"])

    if kind == "Income":
        agg["total"] = -agg["total"]

    col1.dataframe(agg)
    fig = px.line(agg, x="month", y="total", title=kind)
    col2.plotly_chart(fig)


agg("Expenses")
agg("Income")


# %%
# calculate each months' difference
diff_val = df.diff(axis=1)
# display(diff_val)

# calculate each months' difference in percentage. display as percentage string
diff_pct = df.pct_change(axis=1).applymap(lambda x: f"{x:.2%}")
# display(diff_pct)

# combine diff_val (use .2f format) and diff_pct
diff = diff_val.applymap(lambda x: f"{x:+.2f}") + " (" + diff_pct + ")"
# ignore "0.00 (0.00%)	"
diff = (
    diff.replace("+0.00 (0.00%)", "same")
    .replace("+0.00 (nan%)", "same")
    .replace("+nan (nan%)", "nan")
)
# display(diff)

# %%
# combine df and diff

# unstack df
df_unstack = df.unstack().to_frame().reset_index().rename(columns={0: "total (CNY)"})
diff_unstack = diff.unstack().to_frame().reset_index().rename(columns={0: "diff"})

# join df and diff on (account, year, month)
merged = pd.merge(df_unstack, diff_unstack, on=["account", "year", "month"])
merged = merged.pivot(
    index="account", values=["total (CNY)", "diff"], columns=["year", "month"]
)
# display(merged)
merged = merged.stack(level=0)
# pub total before diff
merged = merged.reindex(["total (CNY)", "diff"], level=1)
# display(merged)

st.write("### Difference with previous month")
st.dataframe(merged, use_container_width=True)


# %%
st.write("## Expenses pie chart")

expenses = df[df.index.str.contains("Expenses")]
# Select month and draw pie chart
month = st.selectbox("Select month", expenses.columns[::-1])
expenses = expenses[month]

df = expenses.to_frame().reset_index()
df.columns = ["account", "total"]

fig = px.pie(
    df, values="total", names="account", title=f"Expenses in {month} (Pie Chart)"
)
st.plotly_chart(fig)

total_all = df["total"].sum()
df["percentage"] = df["total"].apply(lambda x: f"{x/total_all:.2%}")
# calculate parent account
parents = []

from collections import defaultdict

parent_total = defaultdict(float)
for account in df["account"]:
    parts = account.split(":")
    parent = ":".join(parts[:-1])
    parents.append(parent)
    parent_total[parent] += df[df["account"] == account]["total"].values[0]

    for i in range(2, len(parts)):
        parent = ":".join(parts[:-i])
        parent_total[parent] += df[df["account"] == account]["total"].values[0]


df["parent"] = parents
for parent, total in parent_total.items():
    # FIXME: a parent might have it's own value?
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                {
                    "account": [parent],
                    "total": [total],
                    "parent": [":".join(parent.split(":")[:-1])],
                    "percentage": [f"{total/total_all:.2%}"],
                },
            ),
        ],
        ignore_index=True,
    )


fig = px.sunburst(
    df,
    values="total",
    names="account",
    parents="parent",
    title=f"Expenses in {month} (Sunburst Chart)",
    branchvalues="total",
    hover_data=["percentage"],
)
st.plotly_chart(fig)

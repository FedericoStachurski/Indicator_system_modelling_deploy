import marimo

__generated_with = "0.4.0"  # adjust to your marimo version

app = marimo.App()

@app.cell
def _(mo):
    x = mo.ui.slider(0, 100, value=50)
    x
    return x

@app.cell
def _(x):
    f"The value squared is {x.value ** 2}"

import calendar

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from datetime import date
from datetime import datetime as dt
from util.constants import *


def layout(df, transaction_category_array,
           category_budget_hash, table):
    return dbc.Card([dbc.CardBody([html.Div([

    html.H1("Budgets"),
    html.P("Manage your personal budgets to manage your money effectively."),
    dbc.Row([
        dbc.Col(
            dbc.Select(
                id="budget-month-select",
                options=[
                    {"label": f"{calendar.month_abbr[i]} 2020",
                     "value": f"2020-{i}"} for
                    i in range(1, dt.today().month + 1)
                ],
                value="2020-08",
            ),
            width=8,
        ),
        dbc.Col([
            dbc.Button("Update Budget", color="info",
                       id="open-add-budget-modal",),
            dbc.Button("Remove Budget", color="danger",
                       id="open-remove-budget-modal"),
        ],
        id="column-with-budget-buttons",
        width=4,
        ),
        dbc.Tooltip("add a new budget or update an existing one",
                    target="open-add-budget-modal"),
        dbc.Tooltip("remove an existing budget",
                    target="open-remove-budget-modal"),

    ], no_gutters=True, style=MARGIN_BELOW_USER_SELECTION_ROW),
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "Modify Chart",
                id="collapse-button",
                className="mb-3",
                color="primary",
            ),
            dbc.Collapse(
                html.Div("this is a div of sorts", className="happy-div"),
                id="collapse",
                className="collapse-style"
            ),
            dcc.Graph(
                id="budget-bar-chart", config=CONFIG,
                style={"height": "30vh"}
            ),
        ]),  
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Span(html.Span(id="budget-card-text")),
                ),
                id="card-for-budget-chart"
            ), width=4
        ),
    ], no_gutters=True, style=MARGIN_BELOW_CHARTS_ROW),
    dbc.Modal([
        dbc.ModalHeader("Add a new budget"),
        dbc.ModalBody([
            dbc.Label("Select a Budget"),
            dbc.Select(
                id="modal-budget-dropdown",
                options=[
                    {"label": key, "value": key} for
                    key in sorted(transaction_category_array)
                ],
            ),
            dbc.Label("Amount per Month ($)"),
            dbc.Input(type="number", id="modal-amount-for-budget"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", color="danger",
                       id="close-add-budget-modal",className="ml-auto"),
            dbc.Button("Save", color="success",
                       id="save-budget-modal", className="ml-auto"),
        ])
    ], id="modal-backdrop"),
    dbc.Modal([
        dbc.ModalHeader("Remove Budget"),
        dbc.ModalBody([
            dbc.Label("Select a Budget to Remove"),
            dbc.Select(
                id="remove-budget-category-dropdown",
                options=[
                    {"label": key, "value": key} for key in category_budget_hash
                ],
            ),
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", color="danger",
                       id="close-remove-budget-modal",className="ml-auto"),
            dbc.Button("Remove", color="success",
                       id="save-remove-budget-modal", className="ml-auto"),
        ])
    ], id="modal-remove-budget-backdrop"),
    html.H1("Insights"),
    html.P(
        (
            "This section breaks down your spending by category. "
            "Use the datepicker to select date range."
        )
    ),
    # datepicker
    dcc.DatePickerRange(
        id="date-picker-for-pie",
        min_date_allowed=min(df["Date"]),
        max_date_allowed=max(df["Date"]),
        start_date=date(2020, 1, 1),
        end_date=dt.now(),
        display_format="YYYY MMM DD",
        style=MARGIN_BELOW_USER_SELECTION_ROW,
    ),
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id="insights-bar-chart",
                style={"height": "40vh"},
                config=CONFIG
            ),
            width=3
        ),
        dbc.Col(
            dcc.Graph(id="pie-chart", config=CONFIG, style={"height": "40vh"}),
            width=5,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H3("Spending by Category"),
                    html.Span(html.Span(id="insights-card-text")),
                ]),
            ), width=4
        ),
    ], no_gutters=True, style=MARGIN_BELOW_CHARTS_ROW),
    html.H1("Transactions"),
    dbc.Row([
        dbc.Col(
            [
                dbc.Checklist(
                    options=[
                        {"label": "Smooth", "value": "smooth"},
                        {"label": "Toggle Grid", "value": "toggleGrid"},
                    ],
                    value=["smooth"],
                    id="checklist-inline-input",
                    inline=True,
                ),
            ]
        ),
    ], no_gutters=True),
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id="transactions-line-chart", config=CONFIG,
                style={"height": "60vh"},
            )
        ),
        dbc.Col(
            table,
            width=4
        ),
    ], no_gutters=True)
])])])

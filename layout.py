import calendar

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from datetime import date
from datetime import datetime as dt
from util.constants import *


def layout(df, transaction_category_array,
           category_budget_hash, table):
    return html.Div([
        dbc.Card([
        dbc.CardBody([
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
            className="col-md-12 col-lg-8"
        ),
        dbc.Col(
            dbc.Button(
                "Update Budget",
                id="open-add-budget-modal",
                color="info",
            ),
            className="col-md-6 col-lg-2"
        ),
        dbc.Col(
            dbc.Button(
                "Remove Budget",
                id="open-remove-budget-modal",
                color="danger",
            ),
            className="col-md-6 col-lg-2"
        ),
        dbc.Tooltip("Add a new budget or update an existing one",
                    target="open-add-budget-modal"),
        dbc.Tooltip("Remove an existing budget",
                    target="open-remove-budget-modal"),

    ], no_gutters=False, style=MARGIN_BELOW_CHARTS_ROW),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id="budget-bar-chart", config=CONFIG,
            ),
        ], width=8, md=12, lg=8),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Span(html.Span(id="budget-card-text")),
                ),
                id="card-for-budget-chart"
            ), width=4, md=12, lg=4
        ),
    ], no_gutters=False, style=MARGIN_BELOW_CHARTS_ROW),
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
        dbc.ModalFooter(html.Div([
            dbc.Button("Save", color="success", id="save-budget-modal",
                       className="ml-auto margin-right"),
            dbc.Button("Close", color="danger", id="close-add-budget-modal",
                       className="ml-auto"),
        ])
        )
    ], className="", id="modal-backdrop"),
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

    ])], className="a-card"),
    dbc.Card([
    dbc.CardBody([

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
        style=MARGIN_BELOW_CHARTS_ROW,
    ),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id="pie-chart", config=CONFIG),
            xs=6, md=4, lg=3,
        ),
        dbc.Col(
            dcc.Graph(
                id="insights-bar-chart",
                config=CONFIG
            ),
            xs=6, md=8, lg=5,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H3("Spending by Category"),
                    html.Span(html.Span(id="insights-card-text")),
                ]),
            ),
            xs=12, md=12, lg=4,
        ),
    ], no_gutters=False, style=MARGIN_BELOW_CHARTS_ROW),

    ])], className="a-card"),
    dbc.Card([
    dbc.CardBody([


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
            ],
        ),
    ], no_gutters=False),
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id="transactions-line-chart", config=CONFIG,
            ),
            width=8, md=12, lg=8
        ),
        dbc.Col(
            table,
            width=4, md=12, lg=4
        ),
    ], no_gutters=False)
])], className="a-card")

])

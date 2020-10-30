import calendar
import datetime
import json
import random

import dash
import dash_auth
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import flask
import plotly
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input, Output, State
from datetime import date
from datetime import datetime as dt
from flask import request

from layout import layout
from util.users import users_info
from util.constants import *

user_pwd, user_names = users_info()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.MINTY],
    suppress_callback_exceptions=True
)
server = app.server

@app.server.route("/login", methods=["POST"])
def route_login():
    data = flask.request.form
    username = data.get("username")
    password = data.get("password")

    if username not in user_pwd.keys() or  user_pwd[username] != password:
        return flask.redirect("/login")
    else:
        rep = flask.redirect("/")
        rep.set_cookie("custom-auth-session", username)
    
        return rep

@app.server.route("/logout", methods=["POST"])
def route_logout():
    rep = flask.redirect("/login")
    rep.set_cookie("custom-auth-session", "", expires=0)
    return rep

def string_date_to_date_object(dateString):
    y, m, d = dateString.split("-")
    y = int(y)
    m = int(m)
    d = int(d[:2])
    return date(y, m, d)

def filter_dataframe_between_two_datetimes(df_filter, start_date, end_date):
    mask = (
        (df_filter["Date"] > start_date) &
        (df_filter["Date"] <= end_date)
    )
    return df_filter.loc[mask]

def filter_dataframe_one_month(df_filter, yearMonth):
    """ yearMonth: "2020-08" -> August, 2020 """
    year, month = yearMonth.split("-")
    year = int(year)
    month = int(month)
    last_day_in_month = num_of_days_in_month(year, month)
    mask = (
        (df_filter["Date"] >= date(year, month, 1)) &
        (df_filter["Date"] <= date(year, month, last_day_in_month))
    )
    return df_filter.loc[mask]

def budget_dataframe_to_hash(json_budget_df):
    budget_df = pd.read_json(json_budget_df, orient='split')

    category_budget_hash = {}
    for idx, row in budget_df.iterrows():
        category_budget_hash[row["Category"]] = row["Budget"]

    return category_budget_hash

def num_of_days_in_month(year, month):
    year = int(year)
    month = int(month)

    if month == 12:
        return (date(year+1, 1, 1) - date(year, month, 1)).days
    else:
        return (date(year, month+1, 1) - date(year, month, 1)).days

def sum_of_category_expense_in_month(df_filter, category, yearMonth="2020-8"):
    df_filter = df_filter[df_filter["Category"] == category]
    df_filter = filter_dataframe_one_month(df_filter, yearMonth)
    sum_of_amounts = df_filter["Amount"].sum()
    return round(sum_of_amounts, 2)

def sum_of_category_expense_between_dates(df_filter, category,
                                          start_date, end_date):
    df_filter = df_filter[df_filter["Category"] == category]
    df_filter = filter_dataframe_between_two_datetimes(
        df_filter, start_date, end_date
    )
    sum_of_amounts = df_filter["Amount"].sum()
    return round(sum_of_amounts, 2)

# login_form = dbc.Form(
#     [
#         dbc.FormGroup(
#             [
#                 dbc.Label("Email", className="mr-2"),
#                 dbc.Input(type="email", placeholder="Enter email"),
#             ],
#             className="mr-3",
#         ),
#         dbc.FormGroup(
#             [
#                 dbc.Label("Password", className="mr-2"),
#                 dbc.Input(type="password", placeholder="Enter password"),
#             ],
#             className="mr-3",
#         ),
#         dbc.Button("Submit", color="primary"),
#     ],
#     inline=True,
# )


login_form = html.Div([
    dbc.Row([
        dbc.Col(
            width=12,
            children=[
                html.Form([
                    dbc.Label("Username"),
                    dbc.Input(placeholder="username", name="username",
                              type="text", id="username-input", value="bob"),
                    dbc.Label("Password"),
                    dbc.Input(placeholder="password", name="password",
                              type="password", id="password-input", value="bob@123"),
                    html.Br(),
                    html.Button("Login", className="btn btn-block btn-primary",
                                type="submit", id="submit-button"),
                ], action="/login", method="post")
            ]
        ),
    ]),
], id="login-form-div")

#     html.Form([
#         dbc.Label("Username"),
#         dbc.Input(placeholder="username", name="username",
#                   type="text", id="username-input", value="bob"),
#         dbc.Label("Password"),
#         dbc.Input(placeholder="password", name="password",
#                   type="password", id="password-input", value="bob@123"),
#         html.Br(),
#         html.Button("Login", className="btn btn-block btn-primary",
#                     type="submit", id="submit-button"),
#     ], action="/login", method="post")
# ], id="login-form-div")

def load_budget_dataframe(session_cookie):
    df = pd.read_csv("data/" + session_cookie + "_budget.csv")
    return df

def load_dataframe(filename):
    df = pd.read_csv("data/" + filename + ".csv")
    df["Date"] = df["Date"].apply(
        lambda d: dt.strptime(d, "%m/%d/%Y").date()
    )

    balance_col = [7757.00]
    balance = balance_col[0]
    for idx, row in df.iterrows():
        if ("Income" in row["Category"] or
            row["Category"] == "Credit Card Payment"):
            balance -= row["Amount"]
        elif (row["Category"] == "Transfer" and
              row["Description"].startswith("E-TRANSFER")):
            balance -= row["Amount"]
        else:
            balance += row["Amount"]

        balance = round(balance, 2)
        balance_col.append(balance)

    df["Balance"] = balance_col[:-1]
    return df

def jsonified_data_to_dataframe(jsonified_data):
    clean_df = pd.read_json(jsonified_data, orient='split')
    clean_df["Date"] = clean_df["Date"].apply(
        lambda d: d.date()
    )
    return clean_df

def transactions_line_chart(dataframe, start_date, end_date, checklistInput):
    df_filtered = filter_dataframe_between_two_datetimes(
        dataframe,
        start_date,
        end_date
    )

    if "smooth" in checklistInput:
        shape = "spline"
    else:
        shape = None

    fig = go.Figure(data=[
        go.Scatter(
            name="all time",
            x=dataframe["Date"],
            y=dataframe["Balance"],
            marker=dict(color="#aaa"),
            line=dict(
                width=1,
                dash="dot",
                smoothing=True,
                shape=shape
            ),
        ),
        go.Scatter(
            name="spending",
            x=df_filtered["Date"],
            y=df_filtered["Balance"],
            marker=dict(color=GREEN_COLOR),
            line=dict(
                width=2,
                smoothing=True,
                shape=shape
            )

        ),
    ])

    showgrid = (True if "toggleGrid" in checklistInput else False)

    fig.update_layout(
        margin=dict(l=10,r=10,t=10,b=10),
        plot_bgcolor=PLOT_BGCOLOR,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        hoverlabel=dict(
            bgcolor="#fafafa",
            font_size=13,
            bordercolor="#555",
        )
    )
    fig.update_xaxes(
        tickangle=-45,
        showspikes=True,
        spikecolor="#bababa",
        spikesnap="cursor",
        spikemode="across",
        spikethickness=1,
        spikedash="dot",
        gridcolor=GRID_COLOR,
        showgrid=showgrid,
        tickmode="array",
    )
    fig.update_yaxes(
        zeroline=False,
        gridcolor=GRID_COLOR,
        showgrid=showgrid,

    )
    return fig

def budget_bar_chart(dataframe, category_budget_hash, yearMonth="2020-08"):
    keys = list(category_budget_hash.keys())
    fig = go.Figure(data=[
        go.Bar(
            name="$ budget",
            y=keys,
            x=[category_budget_hash[k] for k in keys],
            marker=dict(color="#ccc"),
            orientation="h",
        ),
        go.Bar(
            name="$ spent",
            y=keys,
            x=[sum_of_category_expense_in_month(dataframe, k, yearMonth)
               for k in keys],
            marker=dict(color=GREEN_COLOR),
            orientation="h",
        ),
    ])

    fig.update_traces(marker_line_width=0, opacity=0.9)
    fig.update_layout(
        barmode="group", bargap=0.2, title="Budget Goals",
        margin=dict(l=0,r=0,t=50,b=0), plot_bgcolor=PLOT_BGCOLOR,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
    )
    return fig

def insights_bar_chart(user_df, start_date_dt, end_date_dt,
                       transaction_category_array):
    df_filter = filter_dataframe_between_two_datetimes(
        user_df, start_date_dt, end_date_dt
    )
    values = []
    labels = []
    for category in transaction_category_array:
        df_by_categ = df_filter[df_filter["Category"] == category]
        category_sum = round(df_by_categ["Amount"].sum(), 2)

        if category_sum > 0:
            values.append(category_sum)
            labels.append(category)

    fig = go.Figure(data=[
        go.Bar(
            name="$",
            y=labels,
            x=values,
            marker=dict(color=GREEN_COLOR),
            orientation="h",
        ),
    ])
    fig.update_traces(marker_line_width=0, opacity=0.9)
    fig.update_layout(
        barmode="group",
        bargap=0.2,
        margin=dict(l=0,r=0,t=50,b=0),
        plot_bgcolor=PLOT_BGCOLOR,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
    )
    return fig

def pie_chart_and_insights_card(dataframe, start_date, end_date,
                                transaction_category_array):
    df_filter = filter_dataframe_between_two_datetimes(
        dataframe, start_date, end_date
    )
    values = []
    labels = []
    label_value_hash = {}
    for category in transaction_category_array:
        df_by_categ = df_filter[df_filter["Category"] == category]
        category_sum = round(df_by_categ["Amount"].sum(), 2)

        if category_sum > 0:
            label_value_hash[category] = category_sum
            values.append(category_sum)
            labels.append(category)

    start_month = calendar.month_abbr[int(start_date.month)]
    end_month = calendar.month_abbr[int(end_date.month)]
    compact_start_date = f"{start_month} {start_date.day}, {start_date.year}"
    compact_end_date = f"{end_month} {end_date.day}, {end_date.year}"

    pie_chart = go.Figure(
        data=[
            go.Pie(
                values=values,
                labels=labels,
                hoverinfo="percent+label",
                marker=dict(
                    line=dict(color="#fafafa", width=4),
                ),
            )
        ],
        layout=dict(
            showlegend=False,
            margin=dict(b=0, t=0, l=0, r=0),
            piecolorway=[GREEN_COLOR],
        )
    )
    pie_chart.update_traces(textposition="inside", textinfo="percent+label")

    # total spendings
    total_spendings_label = "$" + str(round(sum(values), 2))

    # calculate total income
    total_income_for_period = 0
    if "Income" in label_value_hash:
        total_income_for_period = round(label_value_hash["Income"], 2)
        total_income_for_period = "$" + str(total_income_for_period)

    most_spent_category = "None"
    if len(values) > 0:
        most_spent_category = labels[values.index(max(values))]

    least_spent_category = "None"
    if len(values) > 0:
        least_spent_category = labels[values.index(min(values))]

    text_for_card = [
        html.P(
            f"Between {compact_start_date} and {compact_end_date}",
            className="subtitle_style",
        ),
        html.P(
            [html.Span("Total Spendings:"),
             html.Span(total_spendings_label,
                       className="floatRightStyle")],
        ),
        html.P(
            [html.Span("Total Income for Period:"),
             html.Span(total_income_for_period,
                       className="floatRightStyle")],
        ),
        html.P(
            [html.Span("Most Spent Category:"),
             html.Span(most_spent_category,
                       className="floatRightStyle")],
        ),
        html.P(
            [html.Span("Least Spent Category:"),
             html.Span(least_spent_category,
                       className="floatRightStyle")],
        ),
    ]

    return pie_chart, text_for_card

def table_from_dataframe(df):
    table_headers = ["Date", "Category", "Amount", "Balance"]
    my_table = dash_table.DataTable(
        id="transaction-table",
        columns=[{"name": i, "id": i} for i in table_headers],
        data=df[table_headers].to_dict("records"),
        page_size=10,
        style_as_list_view=True,
        style_table={
        },
        style_cell={
            # 'whiteSpace': 'normal',
            'height': 'auto',
            "color": "#111",
            "textAlign": "left",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#eef",
            }
        ],
        style_cell_conditional=[],
        style_header={
            "backgroundColor": GREEN_COLOR,
            "color": PLOT_BGCOLOR
        }
    )
    return my_table

def serve_layout():
    session_cookie = flask.request.cookies.get("custom-auth-session")

    # landing login page
    if session_cookie not in user_names.keys():
        topnav = html.H1(
            "Log In", style={"textAlign": "center"},
            className="login-title")
        return html.Div([
            html.Div(topnav, id="top-nav"),
            html.Div(login_form, id="app-content"),
            dbc.Alert([
                html.H5("Log in credentials", className="alert-heading"),
                html.Span([
                    html.Span("Usr "),
                    html.B("bob", style=UNDERLINE_STYLE),
                    html.Span(", Pwd "),
                    html.B("bob@123 ", style=UNDERLINE_STYLE),
                ]),
                html.Br(),
                html.Span([
                    html.Span("Usr "),
                    html.B("sally", style=UNDERLINE_STYLE),
                    html.Span(", Pwd "),
                    html.B("sally@123 ", style=UNDERLINE_STYLE),
                ]),
                ],
                color="light",
                id="credentials-alert",
                dismissable=True,
            ),
        ])
    # show the app
    else:
        greeting_and_logout_button = dbc.Row(
            [
                dbc.Col(
                    html.Span(
                        user_names[session_cookie],
                        id="username-greeting",
                    )
                ),
                dbc.Col(
                    dcc.LogoutButton(
                        logout_url="/logout",
                        className="btn btn-outline-dark"
                    ),
                    width="auto",
                )
            ],
            no_gutters=True,
            className="ml-auto flex-nowrap mt-3 mt-md-0",
            align="center",
        )

        topnav = dbc.Navbar([
            dbc.NavbarBrand(
                NAVBAR_TITLE, className="ml-2",
                style=TITLE_STYLE
            ),
            dbc.NavbarBrand(
                NAVBAR_SUBTITLE,
                className="ml-2 subtitle_style"
            ),
            greeting_and_logout_button,
        ],
            color="light",
            light=True,
            id="navbar",
            sticky=True,
        )

        user_df = load_dataframe(session_cookie)
        transaction_category_array = list(user_df.Category.unique())
        budget_df = load_budget_dataframe(session_cookie)
        my_table = table_from_dataframe(user_df)

        json_user_df = user_df.to_json(date_format='iso', orient='split')
        json_budget_df = budget_df.to_json(date_format='iso', orient='split')

        return html.Div([
            html.Div(
                topnav,
                id="top-nav",
            ),
            html.Div(
                layout(user_df,
                       transaction_category_array,
                       {},
                       my_table),
                id="app-content",
            ),
            html.Div(
                json_user_df,
                id="hidden-dataframe",
                className="hiddenDiv",
            ),
            html.Div(
                transaction_category_array,
                id="hidden-transaction-category-array",
                className="hiddenDiv",
            ),
            html.Div(
                json_budget_df,
                id="hidden-budget-data",
                className="hiddenDiv",
            ),
        ])

app.layout = serve_layout

@app.callback(
    Output("modal-backdrop", "is_open"),
    [Input("open-add-budget-modal", "n_clicks"),
     Input("close-add-budget-modal", "n_clicks"),
     Input("save-budget-modal", "n_clicks")],
    [State("modal-backdrop", "is_open")]
)
def toggle_modal_for_add_budget(n1, n2, nSave, is_open):
    if n1 or n2 or nSave:
        return not is_open
    return is_open

@app.callback(
    Output("modal-remove-budget-backdrop", "is_open"),
    [Input("open-remove-budget-modal", "n_clicks"),
     Input("close-remove-budget-modal", "n_clicks"),
     Input("save-remove-budget-modal", "n_clicks")],
    [State("modal-remove-budget-backdrop", "is_open")]
)
def toggle_modal_for_remove_budget(n1, n2, nSave, is_open):
    if n1 or n2 or nSave:
        return not is_open
    return is_open

@app.callback(
    [Output("budget-bar-chart", "figure"),
     Output("modal-budget-dropdown", "value"),
     Output("modal-amount-for-budget", "value"),
     Output("remove-budget-category-dropdown", "value"),
     Output("remove-budget-category-dropdown", "options")],
    [Input("save-budget-modal", "n_clicks"),
     Input("save-remove-budget-modal", "n_clicks"),
     Input("budget-month-select", "value")],
    [State("modal-budget-dropdown", "value"),
     State("modal-amount-for-budget", "value"),
     State("remove-budget-category-dropdown", "value"),
     State("hidden-dataframe", "children"),
     State("hidden-budget-data", "children")]
)
def update_budget_bar_chart(save_add_budget_n, save_remove_budget_n,
                            yearMonth, category_to_update,
                            amount_for_update, category_to_delete,
                            jsonified_data, json_budget_df):
    user_df = jsonified_data_to_dataframe(jsonified_data)
    category_budget_hash = budget_dataframe_to_hash(json_budget_df)

    if category_to_update:
        category_budget_hash[category_to_update] = amount_for_update
    elif category_to_delete:
        del category_budget_hash[category_to_delete]

    new_options = [{"label": key, "value": key} for key in category_budget_hash]

    return [
        budget_bar_chart(user_df, category_budget_hash, yearMonth),
        "", "", "", new_options
    ]

@app.callback(
    Output("budget-card-text", "children"),
    [Input("save-budget-modal", "n_clicks"),
     Input("save-remove-budget-modal", "n_clicks"),
     Input("budget-month-select", "value")],
    [State("hidden-dataframe", "children"),
     State("hidden-budget-data", "children")]
)
def update_budget_card_contents(n1, n2, yearMonth, jsonified_data,
                                json_budget_df):

    user_df = jsonified_data_to_dataframe(jsonified_data)
    category_budget_hash = budget_dataframe_to_hash(json_budget_df)

    budget_total = 0
    funds_spent = 0
    for category in category_budget_hash:
        budget_total += category_budget_hash[category]
        funds_spent += sum_of_category_expense_in_month(user_df, category, yearMonth)

    funds_spent = round(funds_spent, 2)
    budget_total = round(budget_total, 2)

    year, month = yearMonth.split("-")
    year = int(year)
    month_abbr = calendar.month_abbr[int(month)]

    balance = budget_total - funds_spent
    balance_color = (GREEN_COLOR if budget_total - funds_spent > 0 else RED_COLOR)
    progress_percent = 100 * (funds_spent / budget_total)

    if progress_percent <= 90:
        progress_color = "success"
    elif progress_percent > 90 and progress_percent < 100:
        progress_color = "warning"
    else:
        progress_color = "danger"

    balance = round(balance, 2)
    progress_percent = round(progress_percent, 1)

    balance_text = None
    if balance >= 0:
        balance_text = "$" + str(balance)
    else:
        balance_text = "-$" + str(balance)[1:]

    output = [
        html.H3(f"Budget Metrics"),
        html.P(
            f"For {month_abbr}, {year}",
            className="subtitle_style",
        ),
        html.P(
            [html.Span("Budget Total:"),
             html.Span("$" + str(budget_total),
                       className="floatRightStyle")],
        ),
        html.P(
            [html.Span("Funds Spent:"),
             html.Span("$" + str(funds_spent),
                       className="floatRightStyle")],
        ),
        html.P([html.Span("Remaining: "),
            html.Span(
                balance_text,
                style={
                    "color": balance_color,
                    "font-weight": 900,
                    "float": "right",
                }
            )
        ]),
        dbc.Progress(
            str(progress_percent)+"%",
            value=progress_percent,
            color=progress_color,
        )
    ]

    return output

@app.callback(
    [Output("pie-chart", "figure"),
     Output("insights-card-text", "children")],
    [Input("date-picker-for-pie", "start_date"),
     Input("date-picker-for-pie", "end_date")],
    [State("hidden-dataframe", "children"),
     State("hidden-transaction-category-array", "children")]
)
def update_pie_chart_and_insights_card(start_date, end_date, jsonified_data,
                                       transaction_category_array):
    user_df = jsonified_data_to_dataframe(jsonified_data)
    start_date_dt = string_date_to_date_object(start_date)
    end_date_dt = string_date_to_date_object(end_date)

    return pie_chart_and_insights_card(user_df, start_date_dt, end_date_dt,
                                       transaction_category_array)

@app.callback(
    Output("insights-bar-chart", "figure"),
    [Input("date-picker-for-pie", "start_date"),
     Input("date-picker-for-pie", "end_date")],
    [State("hidden-dataframe", "children"),
     State("hidden-transaction-category-array", "children")]
)
def update_insights_bar_chart(start_date, end_date, jsonified_data,
                              transaction_category_array):
    user_df = jsonified_data_to_dataframe(jsonified_data)
    start_date_dt = string_date_to_date_object(start_date)
    end_date_dt = string_date_to_date_object(end_date)

    return insights_bar_chart(user_df, start_date_dt, end_date_dt,
                              transaction_category_array)

@app.callback(
    Output("transactions-line-chart", "figure"),
    [Input("date-picker-for-pie", "start_date"),
     Input("date-picker-for-pie", "end_date"),
     Input("checklist-inline-input", "value")],
    [State("hidden-dataframe", "children")]
)
def update_transactions_line_chart(start_date, end_date, checklistInput,
                                   jsonified_data):

    user_df = jsonified_data_to_dataframe(jsonified_data)
    start_date_dt = string_date_to_date_object(start_date)
    end_date_dt = string_date_to_date_object(end_date)

    chart = transactions_line_chart(
        user_df, start_date_dt,
        end_date_dt, checklistInput,
    )

    return chart

@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

if __name__ == "__main__":
    app.run_server(debug=True)

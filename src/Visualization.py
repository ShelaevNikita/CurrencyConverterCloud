#!/usr/bin/env python3

import plotly.graph_objects as go

from datetime import datetime, timedelta
from dash import Dash, dcc, html, Input, Output, no_update

from src import SpecialSymbols, DataMining

class VisualizationCur():
    
    def __init__(self):
        self.app = Dash(__name__)
        self.dataMiningClass = DataMining.DataMining()
        self.allSymbols = SpecialSymbols.SPECIALSYMBOLS
        self.filterKeys = [keys for (keys, _) in self.allSymbols.items()]
        
    def layout(self):
        self.app.layout = html.Div([
            html.H1('Currency converter', style = {'textAlign':'center'}),
            html.Hr(),
            html.Div([
                html.Div([
                    html.Label('currencyFrom:'),
                    dcc.Dropdown(
                        self.filterKeys,
                        self.filterKeys[12],
                        id = 'currencyFrom'
                    )], style = {'textAlign':'center', 'padding':10, 'flex':1}),
                
                html.Div([
                    html.Label('currencyTo:'),
                    dcc.Dropdown(
                        self.filterKeys,
                        self.filterKeys[0],
                        id = 'currencyTo'
                    )], style = {'textAlign':'center', 'padding':10, 'flex':1}),              
                
                html.Div([
                    dcc.Input(
                        id = 'count',
                        value = 1,
                        type = 'number',
                        min  = 1,
                        step = 1,
                        style = {'textAlign':'center', 'font-size':'large'}
                    )], style = {'padding':33, 'flex':1}),

                html.Div([
                    dcc.DatePickerRange(
                        id = 'dateRange',
                        min_date_allowed = datetime(2020, 1, 1),
                        max_date_allowed = datetime.today(),
                        start_date = datetime.today() - timedelta(days = 1),
                        end_date   = datetime.today(),
                        display_format = 'DD-MM-YYYY'
                )], style = {'textAlign':'center', 'padding':25, 'flex':2})
                              
            ], style = {'display':'flex', 'flexDirection':'row'}),
            
            dcc.Graph(id = 'graph')
        ])

        @self.app.callback(
            Output('graph', 'figure'),
            Input('currencyFrom', 'value'),
            Input('currencyTo',   'value'),
            Input('count', 'value'),
            Input('dateRange', 'start_date'),
            Input('dateRange', 'end_date'))
        def updateGraph(currencyFrom, currencyTo, count, start_date, end_date):

            if currencyFrom is None or currencyTo is None or \
                count is None or start_date is None or end_date is None:
                return no_update
                
            currencyFromName = self.allSymbols[currencyFrom]
            currencyFromTo   = self.allSymbols[currencyTo]
            dateFrom         = datetime.fromisoformat(start_date).date()
            dateTo           = datetime.fromisoformat(end_date).date()
            curCount         = int(count)

            dateArray, resultArray = self.dataMiningClass.getCurrencyValueArray(
                currencyFromName, currencyFromTo, curCount, dateFrom, dateTo)

            dateArray = list(map(lambda x: datetime.strptime(x, '%d-%m-%y').date(), dateArray))
            
            fig = go.Figure(data = go.Scatter(x = dateArray, y = resultArray))
            yaxis_title = currencyFromName.upper() + ' \ ' + currencyFromTo.upper()
            fig.update_layout(xaxis_title = 'Date', yaxis_title = yaxis_title, autosize = True)
            return fig

    def main(self):
        self.dataMiningClass.prepareBD()
        self.layout()
        self.app.run_server(host = '0.0.0.0')

if __name__ == '__main__':
     VisualizationCur().main()

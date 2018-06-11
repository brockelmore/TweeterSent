from flask import Flask, request, jsonify
import base64
import pandas as pd
from sqlalchemy import create_engine
import time
from bokeh.io import save
from bokeh.plotting import figure, show
from bokeh.models.sources import ColumnDataSource
import numpy as np
from bokeh.io import export_png
import os

app = Flask(__name__)

user = ''
password = ''
database = ''
table = ''

def create_graph(terms, vs):
    try:
        db2 = create_engine('mysql+mysqlconnector://{}:{}@localhost/{}'.format(user, password, database), echo=False)
        c = db2.connect()
        start = int(round(time.time() *1000)) - 86400 * 1000     ### Assumes milliseconds as the timestamp from twitter
        query = "SELECT * from {} WHERE tweet LIKE %s".format(table)
        params = []
        title = ""
        
        ### Combined terms. Creates the SQL query and parameters, uses pandas to read the sql database, then bokeh to create the graph.
        if not vs or vs == None:
            for i in range(len(terms)):
                params.append('%'+terms[i]+'%')
                title += terms[i] + ' ' 
                if i != 0:
                    query += ' or tweet LIKE %s'
            query += ' and unix >= %s ORDER BY unix DESC'
            params.append(start)
            title += 'Sentiment'
            df = pd.read_sql(query, c, params=tuple(params))
            df.sort_values('unix', inplace=True)
            df.unix = pd.to_datetime(df.unix, unit='ms')
            df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df)/4)).mean()
            p = figure(width=600, tools=['crosshair','box_zoom','pan', 'reset','wheel_zoom'], toolbar_location=None, title=title, x_axis_type='datetime')#, y_axis_type='log')
            p.line(x=df['unix'], y=df['sentiment_smoothed'], color='cyan', line_width=3)
            smoothed_max = max(df['sentiment_smoothed'])
            smoothed_min = min(df['sentiment_smoothed'])
            
        ### 'vs' for comparing sentiment of various terms, works pretty much the same as above, but separates queries and params.
        if vs:
           print('vs')
           df = pd.DataFrame()
           p = figure(width=600, tools=['crosshair','box_zoom','pan', 'reset','wheel_zoom'], toolbar_location=None, title=title, x_axis_type='datetime')#, y_axis_type='log')
           colors = ['cyan', 'yellow', 'pink']
           for i in range(len(terms)):
               params = []
               query = ""
               title += terms[i] + ' ' 
               params.append('%'+terms[i]+'%')
               params.append(start)
               query = 'SELECT * from {} WHERE tweet LIKE %s and unix >= %s ORDER BY unix DESC'.format(table)
               print(query)
               print(params)
               temp = pd.read_sql(query, c, params=params)
               temp.sort_values('unix', inplace=True)
               temp.unix = pd.to_datetime(temp.unix, unit='ms')
               temp['sentiment_smoothed'] = temp['sentiment'].rolling(int(len(temp)/4)).mean()
               p.line(x=temp['unix'], y=temp['sentiment_smoothed'], color=colors[i], line_width=3)
                
        p.background_fill_color = "black"
        p.border_fill_color = "black"
        p.yaxis.major_label_text_color = "white"
        p.xaxis.major_label_text_color = "white"
        p.ygrid.grid_line_alpha = 0.5
        p.xgrid.grid_line_alpha = 0.5
        p.xaxis.major_tick_line_color = "white"
        p.yaxis.major_tick_line_color = "white"
        p.xaxis.minor_tick_line_color = "white"
        p.yaxis.minor_tick_line_color = "white"
        p.outline_line_alpha = 0.3
        p.outline_line_color = "blue"
        p.title.text_color = "white"
        p.title.align = "center"
        smoothed_max = 0
        smoothed_min = 0

        filename = "{}.png".format(terms[0])
        export_png(p, filename=filename)
        return filename, smoothed_max, smoothed_min ### returns the temporary filename of the chart.png, and max and min values
    except Exception as e:
        return e, "", ''

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>" ### holder for base url

### API handler

@app.route('/graph')
def graph():
    term = request.args.get('term', default='btc')
    term1 = request.args.get('term1', default=None)
    term2 = request.args.get('term2', default=None)
    vs = request.args.get('vs', default=False)
    terms = [term, term1, term2]
    terms = [i for i in terms if i != None]
    file_name, sm_max, sm_min = create_graph(terms, vs)
    try:
        encoded_image = base64.b64encode(open(file_name, 'rb').read()) ### base64 encode the image for handling by the discord bot as they do not run off same server
        encoded_image= str(encoded_image)[2:-1]
        os.remove(file_name)
        return jsonify({'image': encoded_image})
    except:
        return jsonify({'error':file_name})

if __name__ == "__main__":
    app.run(port=5000)

from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests

matplotlib.use('Agg')
app = Flask(__name__)

## Web-Scrap section
url_get = requests.get('https://www.imdb.com/search/title/?release_date=2019-01-01,2019-12-31')
soup = BeautifulSoup(url_get.content,"html.parser")

## Get data from `soup`
container_list = soup.find('div', attrs={'class':'lister-list'})
movielist = container_list.find_all('div', attrs={'class':'lister-item mode-advanced'})

## initiate tuple
temp_movieset = []
titles = []
imdbratings = []
votes = []
metascores = []

## loop ResultSet movielist, get movie info for each movie
for movie in movielist:
    #get titles
    titles = movie.find('div', attrs={'class':'lister-item-content'})\
            .find('h3', attrs={'class':'lister-item-header'})\
            .find('a').text.strip()
    
    #get imdb rating
    imdbratings = movie.find('div', attrs={'class':'lister-item-content'})\
                    .find('div', attrs={'class':'ratings-bar'})\
                    .find('strong').text.strip()                    
    
    #get user's votes
    #vote = container.find('span', attrs = {'name':'nv'})['data-value']
    votes = movie.find('div', attrs={'class':'lister-item-content'})\
            .find('p', attrs={'class':'sort-num_votes-visible'})\
            .find('span', attrs={'name':'nv'}).text.strip()
            #.find('span', attrs={'name':'nv'})['data-value']
    
    #get metascore
    if (movie.find('div', attrs={'class':'lister-item-content'})\
                    .find('div', attrs={'class':'ratings-bar'})\
                    .find('div', attrs={'class':'inline-block ratings-metascore'})) is None:
        metascores = "<blank>"
    else:
        metascores = movie.find('div', attrs={'class':'lister-item-content'})\
                    .find('div', attrs={'class':'ratings-bar'})\
                    .find('div', attrs={'class':'inline-block ratings-metascore'}).contents[1]\
                    .contents[0]
                    #.find('span')#stript.strip()
                    #.find('span', class_=re.compile("metascore"))#.text.strip()
                    
    #temp_movieset.append((titles, float(imdbratings), int(votes), metascores))
    temp_movieset.append((titles, imdbratings, votes, metascores))
#end loop

## Set listDataMovie into dataframe
df = pd.DataFrame(temp_movieset, columns=('title', 'imdb_rating', 'users_vote', 'metascore')) 

## insert data wrangling here
df['imdb_rating'] = df['imdb_rating'].astype('float64')
df['users_vote'] = df['users_vote'].str.replace(',','')
df['users_vote'] = df['users_vote'].astype('int')
df.drop('metascore', inplace=True, axis=1)
df = df.set_index('title')

# reshaping df for (Q1)
topseven_by_imdbrating = df.sort_values('imdb_rating')['imdb_rating'].head(6).reset_index()
x_axis = topseven_by_imdbrating['title']
y_axis = topseven_by_imdbrating['imdb_rating']
#end of reshaping (Q1)

# reshaping df for `stats`
df_mostvotesmovie = df.reset_index().sort_values('users_vote', ascending = False)\
                [['title', 'users_vote', 'imdb_rating']]
#end of reshaping `stats`

##end of data wranggling 

@app.route("/")
# This fuction for rendering the table
def index():
    stats = {
        'most_categories' : df_mostvotesmovie['users_vote'].iloc[0],
        'total': df_mostvotesmovie['title'].iloc[0],      
        # rev_table contains top 10 popular movies based on IMDb user vote
        'rev_table' : df_mostvotesmovie.head(10).reset_index()[['title', 'users_vote', 'imdb_rating']].to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## [1]Barh Plot (most popular movie by `imdb_score`)
    topseven_by_usersvote = df.sort_values('users_vote')['users_vote'].head(6).reset_index()
    x_axis = topseven_by_usersvote['title']
    y_axis = topseven_by_usersvote['users_vote']
    
    fig = plt.figure(figsize=(13,7),dpi=300)
    fig.add_subplot()
    
    plt.barh(x_axis, y_axis, color='crgbkym')
    plt.xlabel('Users Vote', fontsize=16)
    plt.ylabel('Title', fontsize=16)
    #store the plot figure into *.png image format
    plt.savefig('cat_order.png',bbox_inches="tight") 

    # convert matplotlib png into base64
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    
    result = str(figdata_png)[2:-1]
    
    ## [2]Scatter Plot (result2) >> {users_vote vs imdb_rating}
    ## Barh plot (most popular movie by `imdb_score`)
    topseven_by_imdbrating = df.sort_values('imdb_rating')['imdb_rating'].head(6).reset_index()
    x_axis = topseven_by_imdbrating['title']
    y_axis = topseven_by_imdbrating['imdb_rating']
    
    fig = plt.figure(figsize=(13,7))
    fig.add_subplot()
   
    plt.barh(x_axis, y_axis, color='crgbkym')
    plt.xlabel('imdb rating', fontsize=16)
    plt.ylabel('title', fontsize=16)
    plt.savefig('rev_rat.png',bbox_inches="tight") 

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
   
    result2 = str(figdata_png)[2:-1]
    
    ## [3]Histogram Size Distribution (result3) >> {distribusi frekuensi `imdb_rating`}
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    #plt._______(_____,bins=100, density=True,  alpha=0.75)
    plt.style.use('ggplot')
    plt.hist(df.reset_index()['imdb_rating'], color='m')
    plt.xlabel('IMDb Score')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## [4]Histogram Size Distribution (result3) >> {distribusi frekuensi `users_vote`}
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    #plt._______(_____,bins=100, density=True,  alpha=0.75)
    plt.style.use('ggplot')
    plt.hist(df.reset_index()['users_vote'], color='c')
    plt.xlabel('User Vote' )
    plt.ylabel('Frequency')
    plt.savefig('bar_type.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1] 
     
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)

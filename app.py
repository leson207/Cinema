from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from datetime import datetime
from box import Box

import pickle
import requests
import bs4 as bs
import numpy as np
import pandas as pd
from urllib import parse

import ast

from preprocess_text import text_preprocessing

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    suggestions = get_suggestions()
    return templates.TemplateResponse("home.html", {"request": request, "suggestions": suggestions})

@app.post("/populate-matches", response_class=HTMLResponse)
async def populate_matches(request: Request):
    data = await request.json()
    movies_list = data['movies_list']
    movie_cards = {
        f"https://image.tmdb.org/t/p/original{movie['poster_path']}" if movie['poster_path'] else "/static/movie_placeholder.jpeg":
        [movie['title'], movie['original_title'], movie['vote_average'], 
         datetime.strptime(movie['release_date'], '%Y-%m-%d').year if movie['release_date'] else "N/A", movie['id']]
        for movie in movies_list
    }
    return templates.TemplateResponse('recommend.html', {"request": request, "movie_cards": movie_cards})

clf = pickle.load(open('sentiment_cls.pkl', 'rb'))
vectorizer = pickle.load(open('vectorizer.pkl','rb'))

def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["','')
    my_list[-1] = my_list[-1].replace('"]','')
    return my_list

def convert_to_list_num(my_list):
    my_list = my_list.split(',')
    my_list[0] = my_list[0].replace("[","")
    my_list[-1] = my_list[-1].replace("]","")
    return my_list

def get_suggestions():
    data = pd.read_csv('final.csv')
    return list(data['Title'].str.capitalize())

def fetch_imdb_reviews(imdb_id):
    url = f'https://www.imdb.com/title/{imdb_id}/reviews?ref_=tt_ov_rt'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data: {response.status_code}")
    
    soup = bs.BeautifulSoup(response.text, 'lxml')

    soup_result = soup.find_all("div", {"class": "ipc-html-content-inner-div"})

    reviews_list = []
    reviews_status = []

    for review in soup_result:
        if review.text:
            reviews_list.append(review.text)
            movie_review_list = np.array([text_preprocessing(review.text)])
            movie_vector = vectorizer.transform(movie_review_list)
            pred = clf.predict(movie_vector)
            reviews_status.append('Positive' if pred else 'Negative')
    
    return reviews_list, reviews_status


@app.post("/recommend", response_class=HTMLResponse)
async def recommend(request: Request):
    data=await request.body()
    data=parse.parse_qs(data.decode())
    data['rec_movies_org'][0]
    L=['rec_movies_org','rec_movies','rec_posters','cast_names','cast_chars','cast_profiles',
        'cast_bdays','cast_bios','cast_places','cast_ids', 'rec_vote', 'rec_year', 'rec_ids']
    for key in L:
        data[key]=ast.literal_eval(data[key][0])

    data=Box(data)
    for i, val in enumerate(data.cast_bios):
        data.cast_bios[i]=val.replace(r'\n', '\n').replace(r'\"', '\"')
    for i, val in enumerate(data.cast_chars):
        data.cast_chars[i]=val.replace(r'\n', '\n').replace(r'\"', '\"')

    movie_cards = {data.rec_posters[i]: [data.rec_movies[i], data.rec_movies_org[i], data.rec_vote[i], data.rec_year[i], data.rec_ids[i]] for i in range(len(data.rec_posters))}
    casts = {data.cast_names[i]: [data.cast_ids[i], data.cast_chars[i], data.cast_profiles[i]] for i in range(len(data.cast_profiles))}
    cast_details = {data.cast_names[i]: [data.cast_ids[i], data.cast_profiles[i], data.cast_bdays[i], data.cast_places[i], data.cast_bios[i]] for i in range(len(data.cast_places))}

    reviews_list,reviews_status = fetch_imdb_reviews(data.imdb_id[0]) if 'imdb_id' in data else ([],[])


    movie_rel_date = ""
    curr_date = ""
    if 'rel_date' in data:
        today = str(datetime.today().date())
        curr_date = datetime.strptime(today, '%Y-%m-%d')
        movie_rel_date = datetime.strptime(data.rel_date[0], '%Y-%m-%d')

    movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}

    response={}
    L=['title', 'poster', 'overview', 'rating', 'vote_count','release_date','runtime','status','genres']
    for key in L:
        if key not in data or len(data[key])==0:
            response[key]=''
        else:
            response[key]=data[key][0]
    
    response['request']=request
    response['movie_rel_date']=movie_rel_date
    response['curr_date']=curr_date
    response['movie_cards']=movie_cards
    response['movie_cards']=movie_cards
    response['reviews']=movie_reviews
    response['casts']=casts
    response['cast_details']=cast_details

    return templates.TemplateResponse('recommend.html', response)
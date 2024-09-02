# The script of the game goes in this file.

#Init python things
init python:
    import json
    import random
    import re
    from datetime import datetime
    import xml.etree.ElementTree as ET

# Declare characters used by this game. The color argument colorizes the


define p = Character("Plexa")
define extracted_genres = []
define movie_list = []

#I thought I was having an overflow error so I added a max.
define movie_max = 105

# The game starts here.

label start:

    # Show a background. This uses a placeholder by default, but you can
    # add a file (named either "bg room.png" or "bg room.jpg") to the
    # images directory to show it.

    scene bg room


    #Set the localllama API address.
    $ llama = renpy.input("Where is your local openAI API server? (server):(port): ")
    $ llama_addy = f"http://{llama}/v1/chat/completions/"

    #Show Plexa, our friendly video mascot.
    show plexa happy at left:
        zoom 0.70

    # These display lines of dialogue.
    p "Hello! Let's get to accessing your Plex!"

    #Get the local plex URL & access token from the user.
    $ xml = renpy.input("Copy & Paste a XML URL. You can get this from 'Get info' -> 'View XML': ")
    $ plexurl = xml.split('/library/')[0]
    $ token = xml.split('Plex-Token=')[1]

    #Begin the video suggestion loop.  Loop for-ev-er.
    while True:

        #Get the time to update the bot.
        $ now = datetime.now()
        $ formatted_date = now.strftime("%a %b %d %Y %H:%M %p")

        #Get the list of genres in the user's Plex.
        $ url = f"{plexurl}/library/sections/1/genre?X-Plex-Token={token}"
        $ genres = renpy.fetch(url , json=None, method="GET", timeout=60, result='text')

        #Split each genre into the number,name pairs in an array.
        $ tree = ET.fromstring(genres)
        python:
            for directory in tree.iter("Directory"):
                key = directory.get("key")
                title = directory.get("title")
                extracted_genres.append(f"{key},{title}")

        #Make the genre list random.
        $ random_genres = random.sample(extracted_genres, len(extracted_genres))

        #Setup the localLLM call.
        $ system_message = f"You are a movie expert. The current date is {formatted_date}"
        $ user_message = f"The following are the available movie genres we can select from: ```{random_genres}```. What genre should we pick?  Output your selection in JSON format as a 'genre' object and do not give any explanation. Always give the entire Genre `number,name` pair."
        $ temp = "0.7"
        $ data = { "model": "lmstudio-community/gemma-2-2b-it-q8_0", "messages": [ {"role": "system", "content": system_message}, {"role": "user", "content": user_message}], "temperature": temp, "max_tokens": -1, "stream": False }

        #Make the localLLM call.
        $ comment = renpy.fetch(llama_addy, json=data, method="POST", timeout=60, result='json')

        #Strip the response down to just the answer.
        $ comment = comment['choices'][0]['message']['content'].strip()
        $ comment = json.loads(comment.replace('```json', '').replace('```',''))

        #Select only the genre.
        $ genre = comment['genre']

        #Split up the genre info.
        $ genre = str(genre).split(',')[0]
        $ genre_name = str(comment['genre']).split(',')[1]

        #Construct the genre Plex URL.
        $ url = f"{plexurl}/library/sections/1/genre/{genre}?X-Plex-Token={token}"

        #Fetch the movie list from Plex.
        $ movies = renpy.fetch(url , json=None, method="GET", timeout=60, result='text')

        #Clean up the movie list. Collect title, description, etc.
        $ tree = ET.fromstring(movies)
        $ movie_list = []
        python:
            for video in tree.iter('Video'):
                title = video.get('title', '')
                rating = video.get('rating', '')
                audience_rating = video.get('audienceRating', '')
                year = video.get('year', '')
                summary = video.get('summary', '')
                director = [director.get('tag', '') for director in video.findall('Director')]
                genre = [genre.get('tag', '') for genre in video.findall('Genre')]

                output = (f"Title: `{title}` RottenTomatoes Critic Rating: `{rating}` "
                  f"Audience Rating: `{audience_rating}` Year: `{year}` "
                  f"Summary: `{summary}` Director: `{', '.join(director)}` "
                  f"Genre: `{', '.join(genre)}`")
                movie_list.append(output)


        #We were having a weird error when we had >112 movies.  If more than movie_max we reduce the list. Sorry.
        python:
            if len(movie_list) > movie_max:
                movie_list = random.sample(movie_list, movie_max)
            else:
                movie_list = random.sample(movie_list, len(movie_list))
        $ updated_list = [movie.replace('``', '`N/A`') for movie in movie_list]
        $ movie_list = updated_list
        $ movies = "\n".join(movie_list)

        #Removing special characters just in case they interfered.
        $ movies = re.sub(r'[^\w\s\`]', '', movies)


        #Have Plexa announce what type of movie she's selecting.
        p "Let me make a selection from your [genre_name] movies!"

        #Prepare the localLLM call.
        $ system_message = f"You are a movie expert. The current date is {formatted_date}"
        $ user_message = f"The following are the available movies we can select from: ```{movies}```. What movie should we pick? Give one or two sentences why you picked what you did."
        $ user_message = str(user_message)
        $ temp = "0.7"
        $ data = { "model": "lmstudio-community/gemma-2-2b-it-q8_0", "messages": [ {"role": "system", "content": system_message}, {"role": "user", "content": user_message}], "temperature": temp, "max_tokens": -1, "stream": False }

        #Make the localLLM call.
        $ comment = renpy.fetch(llama_addy, json=data, method="POST", timeout=60, result='text')

        #Clean up the response.
        $ comment = json.loads(comment)

        #Strip it to just the content.
        $ comment = [comment['choices'][0]['message']['content']]

        #Making sure it's a string.
        $ comment = [str(comment)]
        python:
            for line in comment:
                renpy.say(p, line)


        #Resetting the movie list.
        $ movie_list = []

        #Setting the URL to the 'unwatched' videos.
        $ url = f"{plexurl}/library/sections/1/unwatched?X-Plex-Token={token}"

        #Getting the list of unwatched Plex videos.
        $ movies = renpy.fetch(url , json=None, method="GET", timeout=60, result='text')

        #Start to clean up the list.  Extract title, description, etc.
        $ tree = ET.fromstring(movies)
        python:
            for video in tree.iter('Video'):
                title = video.get('title', '')
                rating = video.get('rating', '')
                audience_rating = video.get('audienceRating', '')
                year = video.get('year', '')
                summary = video.get('summary', '')
                director = [director.get('tag', '') for director in video.findall('Director')]
                genre = [genre.get('tag', '') for genre in video.findall('Genre')]

                output = (f"Title: `{title}` RottenTomatoes Critic Rating: `{rating}` "
                  f"Audience Rating: `{audience_rating}` Year: `{year}` "
                  f"Summary: `{summary}` Director: `{', '.join(director)}` "
                  f"Genre: `{', '.join(genre)}`")
                movie_list.append(output)

        #Trying to not error out with >112 movies for some reason.
        python:
            if len(movie_list) > movie_max:
                movie_list = random.sample(movie_list, movie_max)
            else:
                movie_list = random.sample(movie_list, len(movie_list))

        #Putting N/A for blank info.
        $ updated_list = [movie.replace('``', '`N/A`') for movie in movie_list]
        $ movie_list = updated_list

        #Turning the array into a string with newlines between the movies.
        $ movies = "\n".join(movie_list)

        #Strip special characters in case they mess with the localLLM call.
        $ movies = re.sub(r'[^\w\s\`]', '', movies)

        #Have Plexa announce she's checking your unwatched movies.
        p "Let me make a selection from your unwatched movies!"

        #Prepare for the localLLM call.
        $ system_message = f"You are a movie expert. The current date is {formatted_date}"
        $ user_message = f"The following are the available movies we can select from: ```{movies}```. What movie should we pick? Give one or two sentences why you picked what you did."
        $ temp = "0.7"
        $ data = { "model": "lmstudio-community/gemma-2-2b-it-q8_0", "messages": [ {"role": "system", "content": system_message}, {"role": "user", "content": user_message}], "temperature": temp, "max_tokens": -1, "stream": False }

        #Make the localLLM call.
        $ comment = renpy.fetch(llama_addy, json=data, method="POST", timeout=60, result='text')

        #Start to clean up the response.
        $ comment = json.loads(comment)

        #Only show the content.
        $ comment = [comment['choices'][0]['message']['content']]

        #Make sure the comment is a string.
        $ comment = [str(comment)]

        #Say each line.
        python:
            for line in comment:
                renpy.say(p, line)

    # This ends the game.

    return

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
from textblob import TextBlob
from unidecode import unidecode
import time
from sqlalchemy import create_engine

user = ''
password = ''
database = ''
table = ''

db2 = create_engine('mysql+mysqlconnector://{}:{}@localhost/{}'.format(user, password, database), echo=False)
c = db2.connect()

def create_table():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS {} (unix BIGINT unsigned, tweet VARCHAR(400), sentiment double)".format(table))
    except Exception as e:
        print(str(e))
create_table()

#consumer key, consumer secret, access token, access secret.
ckey=""
csecret=""
atoken=""
asecret=""

class listener(StreamListener):

    def on_data(self, data):
        try:
            data = json.loads(data)
            tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']
            analysis = TextBlob(tweet)

            sentiment = analysis.sentiment.polarity
            print(time_ms, tweet, sentiment)
            c.execute("""INSERT INTO %s (unix, tweet, sentiment) VALUES (%s, %s, %s)""", (table, int(time_ms),tweet,sentiment))

        except KeyError as e:
            print(str(e))
        return(True)

    def on_error(self, status):
        print(status)


while True:

    try:
        auth = OAuthHandler(ckey, csecret)
        auth.set_access_token(atoken,asecret)
        twitterStream = Stream(auth, listener())
        twitterStream.filter(track=["a","e","i","o","u"]) ## get anything with a vowel in it.
    except Exception as e:
        print(str(e))
        time.sleep(5)

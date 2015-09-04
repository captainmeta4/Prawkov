import praw
import time
import os
import random

r=praw.Reddit("Markov comment bot")

###Configs

subreddits = [
    'futurology'
    ]

#oauth stuff
client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
r.set_oauth_app_info(client_id,client_secret,'http://127.0.0.1:65010/authorize_callback')


###End Configs

class Bot():

    def auth(self, subredditname):
        r.refresh_access_information(os.environ.get(subredditname))

    def text_to_triples(self, text):
        #generates triples given text

        data = text.split()

        #cancel out on comments that are too short
        if len(data) < 3:
            return

        self.lengths.append(len(data))

        #iterate through triples
        for i in range(len(data)-2):
            yield (data[i], data[i+1], data[i+2])

    def text_to_tuples(self, text):
        #generates tuples given text

        data = text.split()

        #cancel out on comments that are too short
        if len(data) < 2:
            return

        #iterate through triples
        for i in range(len(data)-1):
            yield (data[i], data[i+1])
        

    def generate_corpus(self, subreddit):

        print("generating corpus for /r/"+str(subreddit)+"...")
        #loads comments and generates a dictionary of
        #  {('word1','word2'): ['word3','word4','word5'...]...}

        self.corpus = {}
        self.starters = []
        self.lengths = []
        #for every comment
        for comment in r.get_comments(subreddit, limit=1000):

            #ignore mod comments
            if comment.distinguished =="mod":
                continue
            
            #print("processing comment "+str(i))
            #get 3-word sets
            #add comment starters to starters list
            start_of_comment=True
            
            for triple in self.text_to_triples(comment.body):
                key = (triple[0], triple[1])

                #note valid comment starters
                if start_of_comment:
                    self.starters.append(key)
                    start_of_comment=False

                #add to corpus
                if key in self.corpus:
                    self.corpus[key].append(triple[2])
                else:
                    self.corpus[key] = [triple[2]]

                
        print("...done")
        

    def generate_text(self, text=""):
        
        key = self.create_starter(text)
        sentence = self.continue_text(key)
        print(sentence)
        return sentence


    def continue_text(self, key):
        
        length = random.choice(self.lengths)

        #start the output based on a key of ('word1','word2)
        output = key[0]+" "+key[1]

        #Add words until we hit a sentance-ender or a key not in the corpus
        while (len(output.split())<length
                and not ((output.endswith(".") and not output.endswith("..."))
                   or output.endswith("!")
                   or output.endswith("?")):

            if key not in self.corpus:
                break
            
            next_word = random.choice(self.corpus[key])
            output += " " + next_word

            key = (key[1], next_word)

        return(output)

    def create_starter(self, text):
        #get tuples of a phrase and return a hit for starters

        possible_starters=[]
        for key in self.text_to_tuples(text):
            if key in self.starters:
                possible_starters.append(key)
        
        #if there are any matches, go with it, otherwise choose random starter
        if len(possible_starters) > 0:
            return random.choice(possible_starters)
        else:
            return random.choice(self.starters)

    def get_random_comment(self, subreddit, x):
        #returns a random comment within the newest X

        #reset x to random
        x=random.randint(1,x)

        #get the x'th post and return it
        for comment in subreddit.get_comments(limit=x):
            post = comment
            
        return post

    def run_cycle(self, subredditname):
        
        #refresh token
        self.auth(subredditname)

        subreddit = r.get_subreddit(subredditname)
            
        #remake the corpus
        self.generate_corpus(subreddit)
        
        #Comment on random post from /new
        post = self.get_random_comment(subreddit, 100)
        reply = self.generate_text(text=post.body)
        post.reply(reply)
        
        print("")
            
        #repond to messages
        for message in r.get_unread(limit=None):
            message.mark_as_read()
            reply = self.generate_sentence(text=message.body)
            message.reply(reply)
                
                
    def run(self):
        
        while True:

            for subredditname in subreddits:
                self.run_cycle(subredditname)
                
            time.sleep(60*60)

            

if __name__=="__main__":
    bot=Bot()
    bot.run()

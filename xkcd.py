import praw
import time
import os
import random
import re

r=praw.Reddit("Markov user simulator for /r/xkcd halloween by /u/captainmeta4")

###Configs

#userlist


#oauth stuff
#client_id = os.environ.get('client_id')
#client_secret = os.environ.get('client_secret')
#r.set_oauth_app_info(client_id,client_secret,'http://127.0.0.1:65010/authorize_callback')

###End Configs

class Bot():

    def auth(self):
        #r.refresh_access_information(os.environ.get(username))
        r.login('markov_ghost',os.environ.get('password'), disable_warning=True)

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
        

    def generate_corpus(self, user):

        print("generating corpus for /u/"+str(user)+"...")
        #loads comments and generates a dictionary of
        #  {('word1','word2'): ['word3','word4','word5'...]...}

        self.corpus = {}
        self.starters = []
        self.lengths = []
        
        #for every comment
        for comment in user.get_comments(limit=1000):

            #ignore mod comments
            if comment.distinguished == "moderator":
                continue

            #ignore /r/spam comments
            if str(comment.subreddit) == "spam":
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
        print("Corpus for /u/"+str(user)+" is "+str(len(self.corpus))+" entries")
        

    def generate_text(self, text=""):
        key = self.create_starter(text)
        output = self.continue_text(key)

        #retry if username ping
        if "/u/" in output:
            output = self.generate_text()

        # fix formatting
        output = re.sub(" \* ","\n\n* ",output)
        output = re.sub(" >","\n\n> ",output)
        output = re.sub(" \d+\. ","\n\n1. ", output)

        output += "\n\n---\n\n*Boo! [I'm your ghost!](/r/xkcd/about/sticky?num=2)*"
        
        return output

    def continue_text(self, key):

        #start the output based on a key of ('word1','word2)
        output = key[0]+" "+key[1]
        
        length = random.choice(self.lengths)

        #Add words until we hit text-ending criteria or a key not in the corpus
        while True:

            if (len(output.split())> length and
                ((output.endswith(".") and not output.endswith("..."))
                 or output.endswith("!")
                 or output.endswith("?"))
                ):
                break

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
        
    def get_random_comment(self, x):
        #returns a random comment within the newest X

        #set i to random
        i=random.randint(1,x)

        #get the i'th comment and return it
        for comment in subreddit.get_comments(limit=i):
            post = comment
            
        #make sure it's not a Human post; if so try again
        if r.get_info(thing_id=post.link_id).link_flair_css_class == "human":
            post = self.get_random_comment(x)
        
        
        return post
    
    def get_random_new(self, x):
        #returns a random submission within the top X of /new

        #set i to random
        i=random.randint(1,x)

        #get the i'th post and return it
        for submission in subreddit.get_new(limit=i):
            post = submission

        #make sure it's not a Human post; if so try again
        if post.link_flair_css_class == "human":
            post = self.get_random_new(x)

        return post

    def run_cycle(self, comment=None, user=None):
        
        
        
        if comment:
            user=comment.author
        elif user:
            user=r.get_redditor(user)
        else:
            raise(TypeError)
        
        self.generate_corpus(user)
        
        try:
            text = self.generate_text()
        except:
            return
        
        print(text)
        
        try:
            comment.reply(text)
        except praw.errors.InvalidComment:
            pass

    def stream(self):

        already_done=[]
        print('loading 1000 existing comments...')
        for comment in r.get_comments('xkcd', limit=None):
            already_done.append(comment.id)

        print('...done')

        for comment in praw.helpers.comment_stream(r,'xkcd',limit=None,verbosity=0):
            if comment.id in already_done:
                continue
            yield comment
        
            
    def run(self):

        self.auth()
        
        for comment in self.stream():
            
            #auto-kill at midnight pst
            if time.time()>1477983599:
                break
                
            if comment.author.name in ["markov_ghost", "AutoModerator", "xkcd_bot"]:
                continue
            
            self.run_cycle(comment=comment)

            

if __name__=="__main__":
    bot=Bot()
    bot.run()

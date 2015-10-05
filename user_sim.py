import praw
import time
import os
import random
import re

r=praw.Reddit("Markov user simulator bot by /u/captainmeta4")

###Configs

#userlist
mappings = {
    'chooter':'chooter_sim',
    'cupcake1713':'cupcake1713_sim',
    'Deimorz':'Deimorz_sim',
    'Drunken_Economist':'Drunken_Econ_Sim',
    'ekjp':'ekjp_sim',
    'kn0thing':'kn0thing_sim',
    'KrispyKrackers':'KrispyKrackers_sim',
    'spez':'spez_sim',
    'spladug':'spladug_sim',
    'sporkicide':'sporkicide_sim',
    'xiong_as_admin':'xiong_as_admin_sim',
    'yishan':'yishan_sim'
    }

subreddit = r.get_subreddit('AdminSimulator')

#oauth stuff
client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
r.set_oauth_app_info(client_id,client_secret,'http://127.0.0.1:65010/authorize_callback')

###End Configs

class Bot():

    def auth(self, username):
        r.refresh_access_information(os.environ.get(username))
        #r.login(mappings[username],os.environ.get('password'), disable_warning=True)

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

        # fix formatting
        output = re.sub(" \* ","\n\n* ",output)
        output = re.sub(" >","\n\n> ",output)
        output = re.sub(" \d+\. ","\n\n1. ", output)
        
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

    def run_cycle(self):
        
        #pick a random admin
        userlist=[]
        for admin in mappings:
            userlist.append(admin)
        username = random.choice(userlist)
        
        #auth as correspondign sim bot
        self.auth(username)
        
        user=r.get_redditor(username)
        self.generate_corpus(user)
        
        try:
            text = self.generate_text()
        except:
            return
        
        print(text)
            
        #x% chance of making this as a new post
        #y% chance of making a top-level comment on existing post
        #z% chance of making a child comment
        i = random.randint(1,100)
        
        if i<=int(os.environ.get('submit')):
            #title is first sentence
            title = re.split("(?<=[.?!]) ",text,maxsplit=1)[0]
            #body is everything else, if anything at all
            try:
                body = re.split("(?<=[.?!]) ",text,maxsplit=1)[1]
            except:
                body=""
                
            r.submit(subreddit,title,text=body)
        elif i<=int(os.environ.get('parent')):
            post = self.get_random_new(10)
            post.add_comment(text)
        else:
            comment = self.get_random_comment(100)
            comment.reply(text)
        
        #check inbox and respond to summons
        summon = "/u/"+mappings[username]
        for message in r.get_unread():
            message.mark_as_read()
            if summon not in message.body:
                continue
            
            #Enclosed in try to protect against any subreddit ban
            try:
                message.reply(self.generate_text())
            except:
                pass
            
    def run(self):
        
        while True:
            self.run_cycle()
            time.sleep(int(os.environ.get('delay')))

            

if __name__=="__main__":
    bot=Bot()
    bot.run()

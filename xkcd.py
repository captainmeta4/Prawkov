import praw
import requests
import json
import re
import random

r=praw.Reddit('praw shell captainmeta4')

bad_comics = [
    404
    ]

#collect xkcd transcripts

class Bot():

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

    def add_to_corpus(self, text):
        
        starter = True

        #Add sentence lengths to length list
        for sentence in re.split('(?<=[?.!]) ',text):
            self.lengths.append(len(sentence.split()))

        #start adding keypairs
        for triple in self.text_to_triples(text):
            key = (triple[0], triple[1])

            #note valid sentence starters
            if starter:
                self.starters.append(key)
                starter=False

            #add to corpus
            if key in self.corpus:
                self.corpus[key].append(triple[2])
            else:
                self.corpus[key] = [triple[2]]

            #check if next key will be a starter
            if ((key[0].endswith(".") and not key[0].endswith("..."))
                or key[0].endswith("!")
                or key[0].endswith("?")):
                
                starter=True

    def generate_text(self, text=""):
        
        key = self.create_starter(text)
        output = self.continue_text(key)
        return output


    def continue_text(self, key):
        
        length = random.choice(self.lengths)

        #start the output based on a key of ('word1','word2)
        output = key[0]+" "+key[1]

        #Add words until we hit a sentance-ender or a key not in the corpus
        while True:

            if (len(output.split()) > length
                and ((output.endswith(".") and not output.endswith("..."))
                     or output.endswith("!")
                     or output.endswith("?")
                     )
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
                
    def generate_corpus(self):
        
        self.corpus = {}
        self.starters = []
        self.lengths = []

        #compile regexes once
        descriptors = re.compile("(\[\[|\{\{).+?(\]\]|\}\})")
        
        
        for i in range(1,10+1):



            print(i)

            #assemble api url
            url="http://xkcd.com/%(i)s/info.0.json" % {"i":str(i)}

            response = requests.get(url)
            data = json.loads(response.text)
            transcript = data['transcript']

            #Eliminate title-text and descriptors from transcript
            transcript = re.sub(descriptors,"",transcript)
            print(transcript)

            self.add_to_corpus(transcript)
            self.add_to_corpus(data['alt'])

if __name__=='__main__':
    bot=Bot()
    bot.generate_corpus()
    

import math

def r(a,b):
    """ Reducer used to group the potential recommandations to the targeted user
    Each potentially recommanded friend is inside a tuple with its number of common friend, or -inf if the recommanded friend is already friend with the user
    These tuples will to be stored in a list """
    if a==None or a==[]:
        if b==None or b==[]:
            return []
        if isinstance(b,tuple):
            b=[b]
        return b
    if b==None or b==[]:
        if isinstance(a,tuple):
            a=[a]
        return a
    if isinstance(a,tuple):
        a=[a]
    if isinstance(b,tuple):
        b=[b]
    return a+b



def cleanup(item):
    """ We get rid of the recommandations the user is already friend with
    We sort by ID, then by number of mutual friend and select at least the 10 first
    We output the string in the expected format <USER><TAB><RECOMMANDATIONS> """
    S=item[0]+'\t'    #item[0] is the user id
    if item[1]!=[]:
        J=item[1]
        if isinstance(item[1][0],str):
            J=[item[1]]
        L = sorted(J,key = lambda x: x[0])    #Sort by user id
        M = sorted(L,key = lambda x: x[1],reverse=True)     #Sort by number of mutual friend
        N = filter(lambda item: item[1]!=-(math.inf),M)     #Remove actual friends
        recommandations = list(N)[:10]      #Select at least the 10 first
        #Formating
        for tup in recommandations:
            S+=tup[0]+','
        S=S[:-1]
    return S


# We open the text file located in hdfs

text_file = sc.textFile("hdfs://localhost:54310/user/hduser_/inputFriends/"+"soc-LiveJournal1Adj.txt")

# Separate each line and create RDD list
friendships = text_file.flatMap(lambda line: line.split("\n"))

# Separate by \t
friendships = friendships.map(lambda item: item.split('\t'))

# Remove separation ,
# This creates a list of ids and the first element is our User
friendships = friendships.map(lambda item: [item[0]]+item[1].split(",")) 

# Remove Users that have one friend or less. This is because the single friend won't benefit from any mutuals
friendships = friendships.filter(lambda item: len(item)>2) 

# Keep in memory the existing friendships relationships, and create the potential mutual friend links with a count of 1
friendships = friendships.map(lambda item: [((item[0], F), -(math.inf)) for F in item[1:]] + [((F1, F2), 1) for F1 in item[1:] for F2 in item[1:] if F1!=F2]) 

# Flatten the list to have all the tuples in one big list
friendships = friendships.flatMap(lambda x: x) 

# Reduce to count the number of mutual friends
friendships = friendships.reduceByKey(lambda a,b: a+b) 

#(('33380', '4'), 1) to ('33380', ('4', 1)) : change the key
friendships = friendships.map(lambda a: (a[0][0],(a[0][1],a[1]))) 

# Create list of potential friends for each user
friendships = friendships.reduceByKey(r) 

# Select and format 
friendships = friendships.map(cleanup)



# Save output
friendships.saveAsTextFile("hdfs://localhost:54310/user/hduser_/output"+"friendships")




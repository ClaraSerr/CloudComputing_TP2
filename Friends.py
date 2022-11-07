import math


def r(a, b):
    print(a, b)
    if a == None or a == [] or (isinstance(a, tuple) and a[1] == -(math.inf)):
        if b == None or b == [] or b[1] == -(math.inf):
            return []
        if isinstance(b, tuple):
            b = [b]
        return b
    if b == None or b == [] or b[1] == -(math.inf):
        if isinstance(a, tuple):
            a = [a]
        return a
    if isinstance(a, tuple):
        a = [a]
    if isinstance(b, tuple):
        b = [b]
    return a+b


def cleanup(item):
    S = item[0]+'\t'
    if item[1] != []:
        recommandations = sorted(sorted(item[1]), key=lambda x: x[1])[:10]
        for tup in recommandations:
            S += tup[0]+','
        S = S[:-1]
    return S


text_file = sc.textFile(
    "hdfs://localhost:54310/user/hduser_/inputFriends/"+"soc-LiveJournal1Adj.txt")

friendships = text_file.flatMap(lambda line: line.split("\n")).map(lambda item: item.split('\t')).map(lambda item: [item[0]]+item[1].split(",")).filter(lambda item: len(item) > 2).map(lambda item: [((item[0], F), -(
    math.inf)) for F in item[1:]] + [((F1, F2), 1) for F1 in item[1:] for F2 in item[1:] if F1 != F2]).flatMap(lambda x: x).reduceByKey(lambda a, b: a+b).map(lambda a: (a[0][0], (a[0][1], a[1]))).reduceByKey(r).map(cleanup)


friendships.saveAsTextFile(
    "hdfs://localhost:54310/user/hduser_/output"+"friends")

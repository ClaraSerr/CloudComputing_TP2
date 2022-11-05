
import os
import pyspark
from pyspark import SparkContext, SparkConf

 
 
if __name__ == '__main__':
    directory = 'input'

    sc = SparkContext('local','PySpark Word Count Exmaple')
    RDD = sc.emptyRDD()
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
    
        if os.path.isfile(f):
            words = sc.textFile(f).flatMap(lambda line: line.split(' '))
            wordMap = words.map(lambda word: (word, 1))
            wordCounts = wordMap.reduceByKey(lambda a,b:a +b)
        RDD=RDD.union(wordCounts)
    RDD = RDD.reduceByKey(lambda x,y : x+y)
# save the counts to output
    RDD.saveAsTextFile(os.getcwd()+'/pysparkOutrmput')


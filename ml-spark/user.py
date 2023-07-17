from pyspark import SparkContext
from matplotlib import *
def draw():
    sc=SparkContext("local[2]","First Spark App")
    user_data=sc.textFile("data/ml-100k/u.user")
    user_fields=user_data.map(lambda line: line.split("|"))
    num_users=user_fields.map(lambda fields: fields[0]).count()
    num_genders=user_fields.map(lambda fields: fields[2]).distinct().count()
    num_occupations=user_fields.map(lambda fields: fields[3]).distinct().count()
    num_zipcodes=user_fields.map(lambda fields: fields[4]).distinct().count()
    print("Users: %d ,genders: %d,occupations: %d, ZIP codes: %d" % (num_users,num_genders,num_occupations,num_zipcodes))
    ages=user_fields.map(lambda x: int(x[1])).collect()
    hist(ages,bins=20,color='lightblue',normed=True)
    fig=matplotlib.pyplot.gcf()
    fig.set_size_inches(16,10)
          
    
    





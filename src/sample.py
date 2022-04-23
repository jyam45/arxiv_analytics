import pandas as pd
import wordcloud as wc
import arxiv_analytics as ax

query = ax.ArxivQuery()

#query.category("cond-mat").AND().comment("dynamics")
#query.category("cs")
query.comment("DAG")
query.max_results(1000)
query.sortby("submittedDate")
query.sortorder("descending")

print(query)

data = ax.ArxivData(query)

#print(data)

collection = data.collect('published')

#print(collection)

trends = data.trend()

print(trends)

wordcloud = data.wordcloud('title')

wordcloud.to_file("wordcloud.png")

#print(wordcloud)



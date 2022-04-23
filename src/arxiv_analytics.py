import urllib, urllib.request
import feedparser as fp
import datetime as dt
import pandas as pd
import wordcloud as wc

# arXiv API User's Manual 
#
#   https://arxiv.org/help/api/user-manual
#

class ArxivQuery :
	def __init__(self,start=0,max_results=10):
		self.API_URL_      = 'http://export.arxiv.org/api/query'
		self.query_list_   = []
		self.id_list_      = []
		self.start_        = start
		self.max_results_  = max_results
		self.sortby_       = None   # { "relevance" | "lastUpdatedDate" | "submittedDate" }
		self.sortorder_    = None   # { "ascending" | "descending" }
		
	def clear( self ):
		self.query_list_.clear()
		self.id_list_.clear()
		self.start_        = 0
		self.max_results_  = 10
		self.sortby_       = None
		self.sortorder_    = None

	def start( self, n ):
		if n >= 0 :
			self.start_ = n
		else:
			raise ValueError("Illegal value.")
		return self

	def max_results( self, n ):
		if n > 0 and n < 30001:
			self.max_results_ = n
		else:
			 raise ValueError("Illegal value.")
		return self

	def sortby( self, text ):
		items = [ "relevance" , "lastUpdatedDate", "submittedDate" ]
		if text in items:
			self.sortby_ = text
		else:
			raise ValueError("Illegal value.")
		return self

	def sortorder( self, text ):
		items = [ "ascending", "descending" ]
		if text in items:
			self.sortorder_ = text
		else:
			raise ValueError("Illegal value.")
		return self

	def title( self, query ):
		self.query_list_.append("ti:"+query)
		return self

	def author( self, query ):
		self.qeury_list_.append("au:"+query)
		return self

	def abstract( self, query ):
		self.query_list_.append("abs:"+query)
		return self

	def comment( self, query ):
		self.query_list_.append("co:"+query)
		return self

	def reference( self, query ):
		self.query_list_.append("jr:"+query)
		return self

	def category( self, query ):
		self.query_list_.append("cat:"+query)
		return self

	def id( self, query ):
		self.id_list_.append(query)
		return self

	def report_number( self, query ):
		self.query_list_.append("rn:"+query)
		return self

	def all( self, query ):
		self.query_list_.append("all:"+query)
		return self

	def AND( self ):
		self.query_list_.append("AND")
		return self

	def OR( self ):
		self.query_list_.append("OR")
		return self

	def ANDNOT( self ):
		self.query_list_.append("ANDNOT")
		return self

	def open_paren( self ):
		self.query_list_.append("(")
		return self

	def close_paren( self ):
		self.query_list_.append(")")
		return self

	def _make_search_query( self ):
		boolean=["AND", "OR", "ANDNOT"]
		needs_boolean=False
		search_query = ""
		for query in self.query_list_:
			if query not in boolean:
				if needs_boolean :
					search_query += "+AND+"
				search_query += query
				needs_boolean = True
			elif query == "(":
				if not needs_boolean:
					search_query += query
				else:
					raise ValueError("Query's syntax error.")
			elif query == ")":
				if needs_boolean:
					search_query += query
				else:
					raise ValueError("Query's syntax error.")
			else:
				if needs_boolean:
					search_query += "+" + query + "+"
					needs_boolean = False
				else:
					raise ValueError("Query's syntax error.")
		if not needs_boolean :
			raise ValueError
		return search_query

	def _make_id_list(self):
		return ' '.join(self.id_list_)

	def __str__(self):
		out_list = [] 

		# search_queryの文字列化
		search_query = self._make_search_query()
		if search_query != "":
			out_list.append( "search_query="+search_query )

		# id_listの文字列化
		id_list = self._make_id_list()
		if id_list != "":
			out_list.append( "id_list="+'"'+search_query+'"' )

		# start
		out_list.append("start="+str(self.start_))

		# max_results
		out_list.append("max_results="+str(self.max_results_))

		# sortBy
		if self.sortby_ is not None:
			out_list.append("sortBy="+self.sortby_)

		# sortOrder
		if self.sortorder_ is not None:
			out_list.append("sortOrder="+self.sortorder_)

		query = self.API_URL_ + "?" + '&'.join(out_list)

		return query

class ArxivData:
	def __init__( self, query ):
		self.stop_list_ = ["a","the","it","is","are","was","were","not","do","did","no","any","there","i","we","to","in","of","for","with","this","that"]
		self.reload(query)

	def reload( self, query ):
		self.query_    = query
		self.raw_data_ = urllib.request.urlopen(str(query))
		self.utf_data_ = self.raw_data_.read().decode('utf-8')
		self.obj_data_ = fp.parse(self.utf_data_)

	def __str__(self):
		return str(self.obj_data_)

	def query(self):
		return self.query_

	def text(self):
		return self.utf_data_

	def parsed(self):
		return self.obj_data_

	def collect(self,tag):
		items=[]
		for entry in self.obj_data_['entries']:
			item = entry[tag].replace('\n','').replace('  ',' ')
			items.append(item)
		return items

	def wordcloud(self,tag,background_color="white",width=800,height=600,stop_words=None):
		# 分析対象の要素から文章を抽出し、１つの文字列にまとめる
		text=""
		for entry in self.obj_data_['entries']:
			text += entry[tag].replace('\n','').replace('  ',' ').replace('.','').replace(',','').lower()
		if text == "":
			raise ValueError("No entry.")
		# 文字列を空白で分割し、意味のない単語リストstop_wordsに登録された単語を削除し、再度連結して１つの文字列にする
		word_list = text.split(' ')
		stop_list = stop_words if stop_words is not None else self.stop_list_
		words = [word for word in word_list if word not in stop_list ]
		text  = ' '.join(words)
		# WordCloudオブジェクトを返却する
		return wc.WordCloud(background_color=background_color,width=width,height=height).generate(text)

	def trend(self):
		# 出版日時をdatetimeオブジェクトに変換し、日単位の検索期間を計算する
		pub_dates = self.collect('published')
		dt_list = []
		for pub_date in pub_dates:
			dt_obj = dt.datetime.strptime(pub_date,'%Y-%m-%dT%H:%M:%SZ')
			dt_list.append(dt_obj)
		if not dt_list : 
			raise ValueError("No entry.")
		period_days = (max(dt_list) - min(dt_list)).days

		# 検索期間に応じて、集計単位を変更する。２ヶ月以下なら日単位、２年以下なら月単位、それ以上は年単位
		if period_days < 61: 
			key_format = "%Y-%m-%d"
			dt_stride  = dt.timedelta(days=1)
		elif period_days < 731:
			key_format = "%Y-%m"
			dt_stride  = dt.timedelta(days=30)
		else:
			key_format = "%Y"
			dt_stride  = dt.timedelta(days=365)

		# 日付をキーにヒストグラムを作成する。
		hist={}
		dt_itr = min(dt_list)
		dt_end = max(dt_list)
		while (dt_end - dt_itr).days >= 0:
			key    = dt.datetime.strftime(dt_itr,key_format)
			hist[key]=0
			dt_itr = dt_itr + dt_stride
		for dt_obj in dt_list:
			key    = dt.datetime.strftime(dt_obj,key_format)
			if not key in hist : hist[key]=0
			hist[key]+=1

		# pandas.DataFrameオブジェクトで返却する
		return pd.DataFrame.from_dict(hist, orient="index", columns=["number of papers"])



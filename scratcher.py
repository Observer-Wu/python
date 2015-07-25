#_*_ coding: utf-8 _*_
#this file is designed to grab some infomaiton from http://xueqiu.com

import re
import sys
import time
import json
import string
import random
import requests

class web_spider:
    def __init__(self):
        #set the header and the opener	
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:33.0) Gecko/20100101 Firefox/33.0',
            'Host': 'xueqiu.com',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
            'Connection': 'keep-alive'
        }
        self.s = requests.session()
        r = self.s.get("http://xueqiu.com", headers = self.header)

    def loadCode(self):
        stocks = []
        with open("stock_name_codes.txt") as fp:
            line = fp.readline()
            while line:
                stock = line.split("\t")
                stocks.append({"code" : stock[0], "name" : stock[1].rstrip()})
                line = fp.readline()
        return stocks	

    #scratch the comment, cid: comment id
    def scratch_comment(self, cid, pages):
        url = 'http://xueqiu.com/service/comments'
        callback = "jQuery183" + repr(random.random()).replace('.', '') + '_' + repr(int(time.time()*1000))
        postdata = {}
        comments = []	
        for page in range(1, pages+1):
            try:
                if page > 1:
                    postdata['page'] = str(page)
                    postdata['asc'] = 'false'
                params = {'filtered':'true', 'id':cid, 'callback':callback}
                r = self.s.post(url, data = postdata, params = params, headers = self.header)
                start = r.text.find('{')
                end = r.text.rfind('}')
                json_comments = json.loads(r.text[start:end+1])['comments']	
                for json_comment in json_comments:
                    comment_name = json_comment['user']['screen_name']
                    commented_name = json_comment['reply_screenName']
                    content = json_comment['text']
                    donate = json_comment['donate_snowcoin']
                    datetime = json_comment['created_at']
                    marvellous = 'true' if donate > 0 else 'false'
                    comment = {
                        'comment_name': comment_name,
                        'commented_name': commented_name,
                        'content': content,
                        'donate': donate,
                        'time': datetime,
                        'marvellous': marvellous
                    }
                    comments.append(comment)
            except Exception as e:
                print 'Exception occured when scratch comment:%s, error:%s' % (json_comment, e)
        return comments

    #scratch deatails 
    def scratch_details(self, jsontext):
        json_details = json.loads(jsontext)['list']
        details = []
        for json_detail in json_details:
            try:
                name = json_detail['user']['screen_name']
                userid = json_detail['user_id']
                topic = json_detail['title']
                content = json_detail['text']
                retweet_count = json_detail['retweet_count'] #转发
                reply_count = json_detail['reply_count']
                donate = json_detail['donate_snowcoin']
                datetime = json_detail['created_at'] / 1000	
                source = json_detail['source']
                comment = self.scratch_comment(json_detail['id'], reply_count/20+1) if reply_count > 0 else None
                detail = {
                    'username': name,
                    'userid': userid,
                    'topic': topic,
                    'content': content, 
                    'retweet_count': retweet_count,
                    'reply_count': reply_count,
                    'donate': donate, 
                    'datetime': datetime,
                    'source': source,
                    'comment': comment
                }
                details.append(detail)
            except Exception as e:
                print 'Exception occured when scratch detail:%s, error:%s' % (json_detail, e)
        return details

    #scratch the discussion section, where the source = user
    def scratch_discussion(self, symbol):
        try:
            url = 'http://xueqiu.com/statuses/search.json'
            params = {
                'count': '15',
                'comment': '0',
                'symbol': symbol,
                'hl': '0',
                'source': 'user',
                'page': '1',
                'sort': 'time',
                '_': repr(int(time.time()*1000))
            }
            r = self.s.get(url, params = params, headers = self.header)
            if r.status_code != 200:
                return
        except Exception as e:
            print 'Exception occured when connect to the discussion page of %s, error:%s' % (symbol, e)
        return self.scratch_details(r.text)

    #scratch the trade section, where the source = trans
    def scratch_trade(self, symbol):
        try:
            url = 'http://xueqiu.com/statuses/search.json'
            params = {
                'count': '15',
                'comment': '0',
                'symbol': symbol,
                'hl': '0',
                'source': 'trans',
                'page': '1',
                '_': repr(int(time.time()*1000))
            } 
            r = self.s.get(url, params = params, headers = self.header)
            if r.status_code != 200:
                return
        except Exception as e:
            print 'Exception occured when connect to the trade page of %s, error:%s' % (symbol, e)
        return self.scratch_details(r.text) 

    #scratch the news section
    def scratch_news(self, symbol):
        try:
            url = 'http://xueqiu.com/statuses/stock_timeline.json'
            params = {
                'symbol_id': symbol,
                'count': '15',
                'source': '自选股新闻',
                'page': '1',
                '_': repr(int(time.time()*1000))
            } 
            r = self.s.get(url, params = params, headers = self.header)
            if r.status_code !=200:
                return	
        except Exception as e:
            print 'Exception occured when connect to the news page of %s, error:%s' % (symbol, e)
        return self.scratch_details(r.text)

    #scratch the notice section
    def scratch_notice(self, symbol):
        try:
            url = 'http://xueqiu.com/statuses/stock_timeline.json'
            params = {
                'symbol_id': symbol,
                'count': '15',
                'source': '公告',
                'page': '1',
                '_': repr(int(time.time()*1000))
            }
            r = self.s.get(url, params = params, headers = self.header)
            if r.status_code != 200:
                return
        except Exception as e:
            print 'Exception occured when connect to the notice page of %s, error:%s' % (symbol, e)
        return self.scratch_details(r.text)

    #combine the code and it's stock exchange
    def symbol_trans(self, stock):
        code = string.atoi(stock)
        if code < 400000:
            stock = 'SZ' + stock
        elif code >= 600000:
            stock = 'SH' + stock
        else:
            stock = 'F:' + stock
        return stock

    def scratch(self):
        #scratch the page
        stocks = loadCode()
        for stock in stocks:
            try:
                symbol = stock['code']
                if symbol.startswith('8'):
                    continue
                symbol = self.symbol_trans(symbol)
                self.scratch_discussion(symbol)	
                self.scratch_trade(symbol)
                self.scratch_news(symbol)
                self.scratch_notice(symbol)
            except Exception as e:
                print 'Exception occured when scratch %s, error:%s' % (stock, e)

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    scratcher = web_spider()
    scratcher.scratch()

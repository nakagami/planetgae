##############################################################################
# Copyright (c) 2011 Hajime Nakagami <nakagami@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
import sys, urllib2, datetime
import feedparser
from google.appengine.ext import db
from django.core.management.base import BaseCommand
from planet.models import Feed, Entry

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        NOW = datetime.datetime.utcnow()
        proxy = kwargs.get('proxy')
        if proxy:
            proxy_handlers = [urllib2.ProxyHandler({"http": proxy})]
        else:
            proxy_handlers = None
        
        for f in Feed.objects.all():
            # Sync RSS feed.
            if proxy_handlers:
                d = feedparser.parse(f.rss_url, handlers = proxy_handlers)
            else:
                d = feedparser.parse(f.rss_url)
        
            if d['feed'].get('title'):
                f.title = d.feed.title
            if d['feed'].get('link'):
                f.link = d.feed.link
            if d['feed'].get('subtitle'):
                f.subtitle = d.feed.subtitle
            if d['feed'].get('author'):
                f.author = d.feed.author
            f.save()
        
            # Sync feed entries.
            for e in d.entries:
                t = e.get('updated_parsed') 
                if t:
                    t = datetime.datetime(*t[:7])
                    if t > NOW:
                        continue
                q = db.Query(Entry)
                q.filter("link=", e.link)
                o = q.get()
                if not o:
                    o = Entry(feed=f) # Add new entry
                    o.link = e.get('link')
                o.title = e.get('title')
                o.description = e.get('description', '')
                o.author = e.get('author', '')
                if t: 
                    o.pub_dttm = t
                    if f.pub_dttm_offset:
                        o.pub_dttm += datetime.timedelta(0, f.pub_dttm_offset * 60)
                elif not o.pub_dttm:
                    o.pub_dttm = NOW
                o.save()


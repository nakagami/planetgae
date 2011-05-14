##############################################################################
# Copyright (c) 2010-2011 Hajime Nakagami <nakagami@gmail.com>
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
from appengine_django.models import BaseModel
from google.appengine.ext import db
from django.conf import settings
from dateutil import zoneinfo, tz

def update_rss():
    import feedparser
    NOW = datetime.datetime.utcnow()
    
    for f in Feed.objects.all():
        # Sync RSS feed.
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
            for o in Entry.all().fetch(1000):
                if e.link==o.link:
                    break

#            q = db.Query(Entry).filter('link=', e.link)
#            o =  q.get()

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


class Feed(BaseModel):
    rss_url = db.StringProperty()
    title = db.StringProperty()
    link = db.StringProperty()
    subtitle = db.StringProperty()
    author = db.StringProperty()
    pub_dttm_offset = db.IntegerProperty(default=0)
    def __unicode__(self):
        if self.title:
            return self.title
        else:
            return self.rss_url

class Entry(BaseModel):
    link = db.StringProperty()
    title = db.StringProperty()
    description = db.TextProperty()
    author = db.StringProperty()
    pub_dttm = db.DateTimeProperty()
    feed = db.ReferenceProperty(Feed, collection_name='entries')
    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.link

    def get_utc_datetime(self):
        t = self.pub_dttm.timetuple()
        return datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5], t[6], tz.tzutc())

    def get_local_datetime(self):
        return self.pub_dttm.replace(tzinfo=tz.tzutc()).astimezone(zoneinfo.gettz(settings.TIME_ZONE))

    def pub_date(self):
        return self.get_local_datetime().date()

    def pub_time(self):
        t = self.get_local_datetime().time()
        return datetime.time(t.hour, t.minute, t.second)

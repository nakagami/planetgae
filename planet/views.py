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
import datetime
from google.appengine.ext.db import djangoforms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from models import update_rss, Entry, Feed

class FeedForm(djangoforms.ModelForm):
    class Meta:
        model = Feed

def pub_dttm_desc(a, b):
    return cmp(b[0].pub_dttm, a[0].pub_dttm)

def index(request):
#    feed_list = Feed.objects.all()
#    entry_list = Entry.objects.select_related().filter(pub_dttm__gte=datetime.date.today()-datetime.timedelta(14)).order_by('-pub_dttm', '-id')
    # FIXME:
    q_feed = Feed.all()
    feed_list = q_feed.fetch(q_feed.count())
    q_entry = Entry.all()
    entry_list = q_entry.fetch(q_entry.count())

    # Create as dict tree 
    dict_tree = {}
    for e in entry_list:
        dict_tree.setdefault(e.pub_date(), {}).setdefault(e.feed, []).append(e)
    days = dict_tree.keys()
    days.sort()
    days.reverse()

    # Recreate as list tree
    recent_list = []
    for day in days:
        blog_list = [dict_tree[day][k] for k in dict_tree[day]]
        blog_list.sort(pub_dttm_desc)
        recent_list.append(blog_list)
        
    return render_to_response('planet/index.html',
            {'feed_list':feed_list, 'recent_list':recent_list})

def syncrss(request):
    update_rss()
    return HttpResponseRedirect('/')

def admin_index(request):
    return render_to_response('planet/admin_index.html', {})

def admin_feed_index(request):
    feed_list = Feed.objects.all()
    return render_to_response('planet/admin_feed.html', {'feed_list':feed_list})

def admin_feed_form(request, feed_id=None):
    if feed_id:
        feed = Feed.get_by_id(int(feed_id))
    else:
        feed = None
    if request.method == 'POST':
        form = FeedForm(request.POST, instance=feed)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.save()
            return HttpResponseRedirect('../')
    else:
        form = FeedForm(instance=feed)
    return render_to_response('planet/admin_feed_form.html', 
            {'feed_id':feed_id, 'form': form})

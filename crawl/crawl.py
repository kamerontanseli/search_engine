import requests, re, operator, itertools
from bs4 import BeautifulSoup
from urlparse import urljoin
from django.db.models import Q, F, FloatField, Sum
from .models import *

ignore_words = set([ "the", "of", "to", "and", "a", "in", "is", "it" ])

class Crawler:
    def __init__(self):
        self.calculate_page_rank()
    
    def calculate_page_rank(self, iterations=1):
        for i in range(iterations):
            print "Iteration %d" % (i)
            for url in UrlList.objects.all():
                PageRank.objects.get_or_create(url=url, defaults={ "score": 1.0 })
                pr = 0.15
                links = url.links_from.all()
                count = links.count()
                if count == 0: continue
                pr += 0.85 * sum(links.values_list("to__ranks__score", flat=True)) / count
                PageRank.objects.update_or_create(url=url, defaults={"score": pr})

    def add_to_index(self, url, soup):
        # index page
        if self.is_indexed(url): return  
        print "Indexing %s" % url 
        text = self.get_text_only(soup)
        words = self.separate_words(text)
        urlid, created = UrlList.objects.get_or_create(url=url) 
        print "Extracting %s ..." % url
        for i in range(len(words)):
            word=words[i]
            if word in ignore_words: continue
            wordid, created = WordList.objects.get_or_create(word=word) 
            WordLocation.objects.create(url=urlid, word=wordid, location=i)
    def get_text_only(self, soup):
        # extract text from a html tag
        v = soup.string
        if v == None:
            c = soup.contents
            result_text = ""
            for t in c:
                subtext = self.get_text_only(t)
                result_text += subtext + '\n'
            return result_text
        else:
            return v.strip()
    def separate_words(self, text):
        # separate text by any non whitespace character 
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != ''] 
    def is_indexed(self, url):
        # return true if this url is already indexed
        u = UrlList.objects.filter(url=url).first() 
        if u != None:
            # check if crawled 
            v = WordLocation.objects.filter(url=u).first()
            if v != None: return True 
        return False
    def add_link_ref(self, url_from, url_to, link_text):
        # Add a link between 2 pages 
        words = self.separate_words(link_text)
        fromid, created = UrlList.objects.get_or_create(url=url_from)
        toid, created = UrlList.objects.get_or_create(url=url_to) 
        if fromid.id == toid.id: return 
        linkid = Link.objects.create(source=fromid, to=toid)
        for word in words:
            if word in ignore_words: continue
            wordid, created = WordList.objects.get_or_create(word=word)
            LinkWord.objects.create(link=linkid, word=wordid)
    def crawl(self, pages, depth=2):
        # crawl pages to specfic depth 
        for i in range(depth):
            new_pages = set()
            for page in pages:
                try:
                    print "Requesting %s ..." % page                    
                    req = requests.get(page)
                except:
                    print "Could not open %s" % page 
                    continue 
                print "Retrieved %s" % page
                soup = BeautifulSoup(req.text)
                self.add_to_index(page, soup)
                links = soup('a')
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url = urljoin(page, link['href'])
                        if url.find("'") != -1: continue
                        url = url.split("#")[0] # remove location 
                        if url[0:4] == 'http' and not self.is_indexed(url):
                            new_pages.add(url)
                        link_text = self.get_text_only(link)
                        self.add_link_ref(page, url, link_text)
            pages=new_pages

class Searcher:

    def page_rank_score(self, rows):
        page_ranks = dict([ (row[0], PageRank.objects.filter(url__id=row[0]).values_list("score", flat=True)[0]) for row in rows ])
        max_rank = max(page_ranks.values())
        normal_scores = dict([ (u, float(1)/max_rank) for (u,l) in page_ranks.items() ])
        return normal_scores

    def get_match_rows(self, q):
        words = q.split(" ")
        word_lists = WordList.objects.filter(reduce(operator.and_, (Q(word__contains=x) for x in words)))
        locations = list(itertools.chain(*[ word.locations.all() for word in word_lists ]))
        return [(loc.url.id, loc.word.id, loc.id) for loc in locations], word_lists.values_list("id", flat=True).distinct() 
        
    def get_scored_list(self, rows, wordids):
        totalscores = dict([ (row[0], 0) for row in rows ])
        weights = [
            (1.0, self.locationscore(rows)),
            (1.0, self.frequency_score(rows)),
            (1.0, self.page_rank_score(rows)),
            (1.0, self.distance_score(rows)),
        ]
        for weight, scores in weights:
            for url in totalscores:
                totalscores[url] += weight * scores[url]    
        return totalscores
    
    def frequency_score(self, rows):
        counts = dict([ (row[0], 0) for row in rows ])
        for row in rows: 
            counts[row[0]] += 1 
        return self.normalize_scores(counts)

    def locationscore(self, rows):
        locations = dict([(row[0], 1000000) for row in rows])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]: 
                locations[row[0]]=loc
        return self.normalize_scores(locations, small_is_better=True)

    def normalize_scores(self, scores, small_is_better=False):
        vsmall = 0.00001 # avoid / 0
        if small_is_better:
            min_score = min(scores.values())
            return dict([ (u, float(min_score) / max(vsmall, l)) for (u,l) in scores.items() ])
        else:
            max_score = max(scores.values())
            if max_score == 0: max_score=vsmall
            return dict([(u, float(c)/max_score) for (u,c) in scores.items()])

    def get_url_name(self, id):
        return UrlList.objects.filter(id=id).values_list("url", flat=True)[0]
    
    def inbound_link_score(self, rows):
        unique_urls = set([ row[0] for row in rows ])
        inboundcount = dict([(u, Link.objects.filter(to__id=u).count()) for u in unique_urls])
        return self.normalize_scores(inboundcount)

    def distance_score(self, rows):
        if len(rows[0]) <= 2: return dict([ (row[0], 1.0) for row in rows ])
        min_distance = dict([ (row[0], 1000000) for row in rows ])
        for row in rows:
            dist = sum([ abs(row[i]-row[i-1]) for i in range(2, len(row)) ])
            if dist < min_distance[row[0]]:
                min_distance[row[0]] = dist 
        return self.normalize_scores(min_distance, small_is_better=True)

    def query(self, q):
        rows, wordids = self.get_match_rows(q)
        if len(rows) < 1 or len(wordids) < 0: return
        scores = self.get_scored_list(rows, wordids)
        ranked_scores = sorted([ (score, url) for (url, score) in scores.items()], reverse=True) 
        return ranked_scores
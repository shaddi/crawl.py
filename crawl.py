from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *
import urlparse
import sys
from BeautifulSoup import BeautifulSoup

# Render a page
class Render(QWebPage):
	def __init__(self, url):
		self.app = QApplication(sys.argv)
		QWebPage.__init__(self)
		self.loadFinished.connect(self._loadFinished)
		self.mainFrame().load(QUrl(url))
		self.app.exec_()
	
	def _loadFinished(self, result):
		self.frame = self.mainFrame()
		self.app.quit()

# rhymes with url, har har
# wrapper for crawl result, builds a result tree
class Earl:
	def __init__(self, value, level, parent=None, children=[]):
		self.value = value
		self.level = level
		self.parent = parent
		self.children = children

	def show(self):
		if self.parent == None:
			momma = "None"
		else:
			momma = str(self.parent.value)
		disp = "%s %s %s\n" % (str(self.level), str(self.value), momma) # note we use spaces since commas can be in urls
		for c in self.children:
			disp += c.show()

		return disp

# the crawler itself
class Crawler:		
	def __init__(self, url_list, max_depth, dots=True, skip_same_domain=False, debug=False):
		self.debug = debug
		self.dots = dots
		self.skip_same_domain = skip_same_domain
		self.url_list = url_list
		self.max_depth = max_depth
		self.results = [] # list of top-level Earls

	# a stupid, stupid filter for non-web links
	def _is_web(self, link):
		if not link.startswith("#") and not link.startswith("javascript:") and not link.startswith("mailto:"):
			return True

	# some guy said this was the fastest way to deduplicate a list in-order. seems legit to me.
	def _dedupe(self, seq, idfun=None):
		if idfun is None:
			def idfun(x): return x
		seen = {}
		result = []
		for item in seq:
			marker = idfun(item)
			if marker in seen: continue
			seen[marker] = 1
			result.append(item)
		return result

	# visit an url. get the final url (after redirects, etc) and the fully rendered html.
	def visit(self, url):
		r = Render(url)
		p = unicode(r.frame.toHtml())
		f_url = str(r.frame.url().toString())
		return [f_url, p]

	# given a url, return a list of all immediately clickable links
	def process(self, url, ttl=10, log=False, strip_dupes=True, debug=False, round_two=False):
		if ttl < 0: return [] # allows us to bound a search

		# pull down and render page
		final_url, page = self.visit(url)

		if self.dots: 
			print '.',
			sys.stdout.flush()
		if debug or self.debug: print final_url + " " + str(ttl)
		
		# parse page
		soup = BeautifulSoup(page)
		
		if(log):
			f = open(final_url + '.log', 'w')
			f.write(soup.prettify())
			f.close()

		
		links = []

		# get anchored links
		for tag in soup.findAll('a', href=True):
			link = tag['href']
			if self._is_web(link):
				l = urlparse.urljoin(final_url,link)
				if round_two:
					links += self.process(l, 0)
				else:
					links.append(l)
		
		# seek and destroy all iframes, harvest their innards
		for tag in soup.findAll('iframe', src=True):
			link = tag['src']
			if self._is_web(link):
				l = urlparse.urljoin(final_url,tag['src'])
				if not final_url == l: # avoid self-loops
					print "%s, %s" % (urlparse.urlsplit(final_url)[1], urlparse.urlsplit(l)[1])
					links += self.process(l, ttl-1, round_two=True) # may not want to skip self on second round... should test this

		# remove duplicates from result list
		if strip_dupes:	
			if self.skip_same_domain:
				links = self._dedupe(links, lambda x: urlparse.urlsplit(x)[1])
			else:
				links = self._dedupe(links)

		# ignore links back to the same domain: it's a quagmire in there
		if self.skip_same_domain: 
			orig_domain = urlparse.urlsplit(final_url)[1]
			links = [l for l in links if not orig_domain == urlparse.urlsplit(l)[1]]

		return links

	# get a url, earlize it, process its links, throw them on the stack
	def crawl(self, url):
		lvl = -1 
		stack = []
		stack.append(Earl(url, 0))
		self.results.append(stack[0]) # keep track of the root

		# standard recursion unroll: intialize stack, pop work off stack, 
		# add new work to stack as encountered
		while len(stack) > 0:
			# earl's the guy you're currently crawling. 
			earl = stack.pop()

			# make a new line for pretty dots at every new level of search
			if self.dots and earl.level > lvl:
				lvl = earl.level
				print ""
				print lvl,
				sys.stdout.flush()

			# get list for all children if we're not already at the limit
			earl.children = [Earl(str(i), earl.level+1, earl) for i in self.process(earl.value)]
			if earl.level < self.max_depth - 1:
				stack += earl.children

		print ""

	# perform a crawl on all the links in this crawler's url list
	def crawl_all(self):
		for u in self.url_list:
			self.crawl(u)

def main():
	depth = int(sys.argv[1])
	urls = sys.argv[2:]
	spiderman = Crawler(urls, depth, dots=False, skip_same_domain=True, debug=False)
	spiderman.crawl_all()
	for r in spiderman.results:
		print r.show()
	
if __name__ == "__main__":
	main()	

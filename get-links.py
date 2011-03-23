from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *
import urllib2
import urlparse
import sys
from BeautifulSoup import BeautifulSoup

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

def is_web(link):
	if not link.startswith("#") and not link.startswith("javascript:"):
		return True

# get the fully-rendered page
def visit(url):
	r = Render(url)
	p = unicode(r.frame.toHtml())
	f_url = str(r.frame.url().toString())
	return [f_url, p]

def process(url):
	final_url, page = visit(url)
	
	soup = BeautifulSoup(page)

	f = open('pretty.log', 'w')
	f.write(soup.prettify())
	f.close()

	links = []

	for tag in soup.findAll('a', href=True):
		link = tag['href']
		if is_web(link):
			l = urlparse.urljoin(final_url,link)
			links.append(l)
	
	print "BITCHES LOVE IFRAMES"
	for tag in soup.findAll('iframe', src=True):
		link = tag['src']
		if is_web(link):
			links += process(urlparse.urljoin(final_url,link))

	return links

def main():
	for url in sys.argv[1:]:
		resolved_links = process(url)
		for i in resolved_links:
			print str(i)

if __name__ == "__main__":
	main()

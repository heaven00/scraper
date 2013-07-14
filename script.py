import urlparse
import os
import facebook
import fbconsole
from urllib2 import urlopen, Request, URLError
from urllib import urlretrieve
from BeautifulSoup import BeautifulSoup
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts
from wordpress_xmlrpc.methods.posts import NewPost, GetPost

DATA_DIR = ''
APP_ID = API_KEY = ''
APP_SECRET = ''
ACCESS_TOKEN = ''
PAGE_ID = ''


def makeSoup(url):
	html = urlopen(url).read()
	soup = BeautifulSoup(html)
	return soup
	
def validate_url(url):
	'validate any url'
	req = Request(url)
	try:
		resp = urlopen(req)
		return True
	except URLError as e:
		print e
		return False
	
def findImageUrls(soup):
	'returns a list of url of images from the hmtl page in the soup'
	images_url = []
	for img in soup.findAll('img'):
		try:
			if img['width'] >= 400 and 'logo.png' not in img['src']:
				images_url.append(img['src'])
		except:
			pass
	return images_url

def downloadImage(urls, out_folder=DATA_DIR):
	'download the images from a list of urls'
	filenames = []
	for url in urls:
		try:
			filename = url.split('/')[-1]
			outpath = os.path.join(out_folder, filename)
			urlretrieve(url, outpath)
			print '==================='
			print 'Downloaded Image %s' % filename
			filenames.append(filename)
		except:
			print 'Failed to download image %s' % filename
	return filenames

def find_next_page(soup, img_src):
	#find all anchor tags and check href for similar link pattern
	possible_next_urls = soup.finAll('a')
	s = img_src.split('/')[:-1]
	match_string = ''
	for parts in s:
		match_string = match_string+s
		match_string = match_string+'/'
	for a in possible_next_urls:
		if a['href'].startswith(match_string):
			url = a['href']
	return url

def find_headers(soup):
	'find the headers corresponding to each image'
	titles = []
	headers = soup.findAll('h2')
	for header in headers:
		titles.append(header.text)
	return titles

def expandUrl(url, depth=3):
	'returns a list of page urls '
	urls = []
	for i in range(1, depth):
		ext = '/page/'+str(i)
		url = urlparse.urljoin(url,ext)
		urls.append(url)
	return urls

def post_data_to_site(titles, filenames):
	post_ids = []
	client = Client('http://domain.com/xmlrpc.php','username','password')
	for i in range(0,len(titles)):
		post_title, filename = titles[i], filenames[i]
		imgfile = os.path.join(DATA_DIR, filename)
		data = {'name':filename, 'type':'image/jpg'}
		with open(imgfile, 'rb+') as img:
			data['bits'] = xmlrpc_client.Binary(img.read())
		response = client.call(media.UploadFile(data))
		attachment_id = response['id']
		post = WordPressPost()
		post.title = post_title
		post.post_status = 'publish'
		post.thumbnail = attachment_id
		post.comment_status = 'open'
		post.id = client.call(posts.NewPost(post))
		post_ids.append(post.id)
		print post.id
	return post_ids	

def extend_access_token(ACCESS_TOKEN):
	graph = facebook.GraphAPI(ACCESS_TOKEN)
	extended_token = graph.extend_access_token(APP_ID, APP_SECRET)
	return extended_token

def share_on_facebook(post_ids, access_token, page_id=PAGE_ID):
	graph = facebook.GraphAPI(access_token)
	client = Client('http://domain.com/xmlrpc.php','username','password')
	for post_id in post_ids:
		post = client.call(GetPost(post_id))
		link = post.link
		path = '/'+str(page_id)+'/feed'
		post = graph.request(path=path,post_args={'link':post.link})
		print post

def main():
	url = 'http://www.lolhappens.com/'
	urls = expandUrl(url,depth=2)
	post_ids = []
	for url in urls:
		soup = makeSoup(url)
		titles = find_headers(soup)
		image_urls = findImageUrls(soup)
		print 'Downloading Images'
		filenames = downloadImage(image_urls)
		print 'Posting to site'
		post_ids.extend(post_data_to_site(titles, filenames))
	#access_token = extend_access_token(ACCESS_TOKEN)
	access_token = ACCESS_TOKEN
	share_on_facebook(post_ids, access_token)
	

if __name__ == '__main__':
	main()

	
	
		
		
	
	
	
	



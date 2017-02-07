from BeautifulSoup import BeautifulSoup as soup
import json, urllib,urllib2, os
VOL_CACHE = 'issue_list.json'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:53.0) Gecko/20100101 Firefox/53.0'
DOMAIN = 'http://link.springer.com/%s'
collection = {}
def parse():
    with open('10643.html', 'r') as source_html:
        soup_html = soup(source_html.read())
        volume_item_list = soup_html.findAll('div', attrs={'class': 'volume-item'})
        for item in volume_item_list:
            #volname = 'volume%d' % i
            #vol_tag = soup_html.find('div', attrs={'id': volname})
            #print vol_tag.find('h2').contents[0].encode('ascii', 'ignore').strip()
            title_tag = item.find('h2')
            volume_num =  title_tag.contents[0].encode('ascii', 'ignore').strip().split(' ')[1]
            collection_key = '%s' % volume_num
            issue_list = []
            issues = item.findAll('a', attrs={'class': 'title'})
            for issue in issues:
                url = DOMAIN % issue['href']
                pub_date_str = issue.contents[0].encode('ascii', 'ignore').strip()
                tmp1 = pub_date_str.split(',')[0].strip()
                tmp2 = pub_date_str.split(',')[1].strip()
                year = tmp1.split(' ')[1]
                month = tmp1.split(' ')[0]
                issue_num = tmp2.split(' ')[1]
                issue_list.append({'url': url, 'year': year, 'month': month, 'issue_num': issue_num})
            
            collection[collection_key] = issue_list


def save_json(save_as, array):
    with open (save_as, 'w') as local_file:
        json.dump({"entry_count": len(array), "content": array}, local_file)
        print '%d entries saved' % len(array)

def download_article_list(issue_url):
    retval = []
    source_html = urllib.urlopen(issue_url)
    soup_html = soup(source_html.read())
    #with open('1.html') as html_source:
    #    soup_html = soup(html_source.read())
    
    links = soup_html.findAll('a', attrs={'id': 'toc-pdf-link'})
    article_count = 0
    
    for link in links:
        title = link['title'].encode('ascii', 'ignore').strip()
        doi = link['doi'].encode('ascii', 'ignore').strip()
        article_url = DOMAIN % link['href'].encode('ascii', 'ignore').strip()
        retval.append({'id': article_count, 'title': title, 'link': article_url, 'doi': doi})
        article_count += 1
    return retval 


def load_json(filename):
    with open(filename, 'r') as local_file:
        cache = json.load(local_file)
        entry_size = cache.get('entry_count')
        content = cache.get('content')
        assert (entry_size == len(content))
    return content


def download_article(url, path, title, info_log, err_log):

    os.system('mkdir -p %s' % path)
    save_as = '%s/%s.pdf' % (path, title.replace(' ', '.'))
    if os.path.isfile(save_as):
        pass
    else:
        try:
            response = urllib2.urlopen(url)
            with open(save_as, 'wb') as fd:
                fd.write(response.read())
            fd.close()
            info_log.write('\n\t\t%s downloaded\n')
        except:
            #print 'downloading %s error' % title
            try:
                os.system('wget %s -O %s/%s.pdf' % (url, path, title))
            except:
                err_log.write('\n\t\t%s downloading error\n' % title)
                err_log.write('\t\tlocal file: %s\n' % path)
                err_log.write('\t\tURL: %s\n\n' % url)
            return 0

    return 1

def load_issue_articles(vol, issue):
    # vol.4.issue.5.jan.2014

    issue_url = issue.get('url')
    year = issue.get('year')
    month = issue.get('month')
    num =  issue.get('issue_num')
    retval = None
    json_path ='json/article_lists/vol.%s.issue.%s.%s.%s.json'  % (vol, num, year, month)
    print 'loading from %s' % json_path
    # has previously saved
    if os.path.isfile(json_path):
        retval  = load_json(json_path)
    else:
        retval  = download_article_list(issue_url)
        save_json(json_path, retval)

    return retval

def main(use_local = False):
    global collection

    total_count = 0
    toc = open('TOC.txt', 'w')
    toc.write('>>>>>> Early Childhood Education Journal\n\n')
    info_log  = open('download_log.txt', 'w')
    err_log  = open('download_err_log.txt', 'w')
    if use_local and os.path.isfile(VOL_CACHE):
        collection = load_json(VOL_CACHE)
    else:
        parse()
        save_json(VOL_CACHE, collection)

    for volume_number in collection.keys():
        issue_list =  collection.get(volume_number)

        volume_article_count = 0
        toc.write('\n\n====================== Vol. %s ====================\n' % volume_number)

        for issue in issue_list:
            issue_url = issue.get('url')
            issue_year = issue.get('year')
            issue_month = issue.get('month')
            issue_num =  issue.get('issue_num')

            issue_article_list = load_issue_articles(volume_number, issue)
            article_count = len(issue_article_list)
            toc.write('\n\t- Issue %s (%d articles)-\n' % (issue_num, article_count))
            downloaded = 0

            path = 'files/Vol.%s.Issue.%s' % (volume_number, issue_num)
            issue_toc = open('%s/table_of_content.txt' % path, 'w')
            issue_toc.write('============ Vol.%s Issue. %s  Table of Content (%d articles) =============\n\n' % (volume_number, issue_num, article_count))
            
            for i in issue_article_list:
                title = i['title']
                doi = i['doi']
                article_url = i['link']
                uid = i['id']
                #print "%d. %s\n%s\n%s\n" % (uid, title, doi, article_url)

                #downloaded += download_article(article_url, path, title, info_log, err_log)
                volume_article_count += 1
                toc.write('\t\t%s\n' % title)
            
            #print 'Vol.%s Issue.%s: downloaded %d/%d' % (volume_number, issue_num, downloaded, article_count)
                info_log.write('Vol.%s Issue.%s: downloaded %d/%d\n\n' % (volume_number, issue_num, downloaded, article_count))
                issue_toc.write("%d. %s\n" % (uid, title))
        toc.write('\n\t%d articles in this volume' % volume_article_count)
        total_count += volume_article_count
    
    toc.write('\n\n>>>>>>>>>>>> %d articles in total <<<<<<<<<<<<<<<' % total_count)
    toc.close()
    err_log.close()
    info_log.close()
if __name__ == '__main__':
    main(use_local=True)
    print 'done'

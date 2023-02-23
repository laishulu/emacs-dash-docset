"""
    Generate Dash docset for the Emacs Editor
    http://www.gnu.org/software/emacs/manual/html_node/emacs/
"""
import sqlite3
import os
import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup as bs
import requests


# docset info
docset_name = 'Emacs.docset'
root_url = 'http://127.0.0.1/'
output = docset_name + '/Contents/Resources/Documents'

# create directory
docpath = output + '/'
if not os.path.exists(docpath): os.makedirs(docpath)
icon = 'https://www.gnu.org/software/emacs/images/emacs.png'

def download(url, path, binary=False):
    res = requests.get(url)
    if binary:
        with open(path, 'wb') as fp:
            fp.write(res.content)
    else:
        with open(path, 'w') as fp:
            fp.write(res.text)

def get_text(url):
    return requests.get(url).text    # for online page

def url_to_request(path):
    return root_url + path

def scrape_root():
    soup = bs(get_text(root_url))
    index = str(soup.find(id='SEC_Contents'))
    open(os.path.join(output, 'index.html'), 'w').write(index)

    for i, link in enumerate(soup.findAll('a')):
        name = link.text.strip()
        path = link.get('href')
        print("path: %s" % path)
        if path.endswith("/") \
                or "/software/emacs/manual/" in path \
                or path.startswith("#"):
            print("skip.....")
            continue

        # figure out directories and create them
        if "/" in path and not "https://" in path and not "http://" in path:

            subdir = path
            folder = os.path.join(docpath)

            # split subdirs
            for i in range(len(subdir.split("/")) - 1):
                folder += subdir.split("/")[i] + "/"

            # add a directory for sub-folder(s)
            if not os.path.exists(folder): os.makedirs(folder)

        print(path, end=' ')
        # download docs and update db
        try:
            print(" V")
            if name and path:
                update_db(name, path)

            print("saving page....")
            if len(path.split('#')) >=2:
                path = path.split('#')[-2]
            if not path.endswith(".html"):
                continue

            url = url_to_request(path)
            download(url, docpath + path)
            print("doc: ", path)

        except Exception as e:
            print(" X")
            print(e)
            exit()
            pass

def download_logo():
    download(icon, docset_name + "/icon.png")

def update_db(name, path):
    typ = 'func'
    cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, typ, path))
    print('DB add >> name: %s, path: %s' % (name, path))

def scrape_keywords_index(url):
    soup = bs(get_text(url))
    for _, td in enumerate(soup.find_all("td", valign="top")):
        if td.text[-1] != ":":
            continue
        name = td.text[:-1].strip()
        path = td.a.get('href')
        print("path: %s" % path)

        # update db
        try:
            print(" V")
            if name and path:
                update_db(name, path)
        except Exception as e:
            print(" X")
            print(e)
            exit()
            pass

def add_infoplist():
    name = docset_name.split('.')[0]
    info = " <?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> " \
           "<plist version=\"1.0\"> " \
           "<dict> " \
           "    <key>CFBundleIdentifier</key> " \
           "    <string>{0}</string> " \
           "    <key>CFBundleName</key> " \
           "    <string>{1}</string>" \
           "    <key>DocSetPlatformFamily</key>" \
           "    <string>{2}</string>" \
           "    <key>isDashDocset</key>" \
           "    <true/>" \
           "    <key>dashIndexFilePath</key>" \
           "    <string>index.html</string>" \
           "</dict>" \
           "</plist>".format(name, name, name)
    open(docset_name + '/Contents/info.plist', 'w').write(info)


if __name__ == '__main__':

    db = sqlite3.connect(docset_name + '/Contents/Resources/docSet.dsidx')
    cur = db.cursor()
    try:
        cur.execute('DROP TABLE searchIndex;')
    except:
        pass
    cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

    # start
    scrape_root()
    scrape_keywords_index(url_to_request("Command-Index.html"))
    scrape_keywords_index(url_to_request("Key-Index.html"))
    scrape_keywords_index(url_to_request("Variable-Index.html"))
    scrape_keywords_index(url_to_request("Concept-Index.html"))
    add_infoplist()

    # commit and close db
    db.commit()
    db.close()

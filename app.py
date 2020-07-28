from bs4 import BeautifulSoup, Comment, NavigableString
from html.parser import HTMLParser
from urllib.parse import urlparse
from textwrap import wrap
import requests
import urllib
import re
import os
import json
import sys
import locale

class PageSaver:
    def __init__(self):
        self.config = {
        # Черный список идентификаторов
        'ids': ['sidebar', 'footer', 'tabloid', 'addition', 'subscribe'],
        # Черный список тегов
        'tags': ['script', 'noscript', 'style', 'iframe', 'svg', 'nav', 'noindex', 'footer'],
        # Черный список классов
        'classes': ['sidebar', 'footer', 'tabloid', 'addition', 'subscribe', 'preview']}

    def get_path(self, url):
        # Получение пути
        cwd = os.getcwd()
        web_path = urllib.parse.urlparse(url)
        hostname = web_path.netloc
        path = web_path.path.replace('/', '\\')
        if path[-1] == '\\':
            path = path[:-1]
        save_here = os.path.join(cwd, hostname, path[1:])
        if not os.path.splitext(save_here)[1]:
            save_here = save_here + '.txt'
        else:
            save_here = os.path.splitext(save_here)[0] + '.txt'
        return save_here

    def update_config(self, cfg):
        # Обновление файла конфигурации
        self.cfg = cfg['common']
        if urllib.parse.urlparse(url).netloc in cfg:
            for key in cfg[urllib.parse.urlparse(url).netloc].keys():
                self.config[key] += cfg[urllib.parse.urlparse(url).netloc][key]

    def clean_html(self, soup):
        for tag in soup.find_all():
            # Удалить пустые теги
            if not tag.get_text(strip=True):
                tag.decompose()
                continue
            # Удалить теги с именем из черного списка
            if tag.name in self.config['tags']:
                tag.decompose()
                continue
            # Удалить теги с классом из черного списка
            if tag.has_attr('class'):
                for cls in self.config['classes']:
                    for cls_name in tag.attrs.get('class'):
                        if cls in cls_name:
                            tag.decompose()
                            break
                    else:
                        continue
                    break
                continue
            # Удалить теги с идентификатором из черного списка
            if tag.has_attr('id'):
                for id in self.config['ids']:
                    if id in tag.attrs.get('id'):
                        tag.decompose()
                        break
                continue
        #
        for tag in soup.find_all():
            for subtag in tag.descendants:
                if isinstance(subtag, NavigableString):
                    if (len(str(subtag).encode('utf-8'))) > len(tag.get_text()) * 2:
                        tag.decompose()
                        break
                    continue
                else:
                    if (len(str(subtag.attrs))) > len(tag.get_text()):
                        tag.decompose()
                        break
                    continue
        # Удалить комментарии
        comments = soup.findAll(text=lambda text:isinstance(text, Comment))
        for comment in comments:
           comment.extract()

    def extract_links(self, soup):
        # Отформатировать ссылки
        for a in soup.find_all('a', href=True):
            a.insert_before('[', a['href'], '] ')
            a.insert_after(a.text)
            a.decompose()

    def add_indents(self, soup):
        # Добавить отступы
        for tag in soup.find_all():
            if tag.name == 'p':
                tag.insert_before('\n\n')

    def write_file(self, soup):
        # Записать в файл
        lines = []
        for line in soup.split('\n'):
            lines.append('\n'.join(wrap(line, 80, break_long_words=False)))
        return '\n'.join(lines)

    def do_magic(self, url):

        soup = BeautifulSoup(requests.get(url).content, 'html.parser').find('body')

        self.clean_html(soup)
        self.extract_links(soup)
        self.add_indents(soup)

        soup = soup.get_text()
        soup = re.sub('\n\n+', '\n\n', str(soup)).strip()

        path = self.get_path(url)

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        file = open(path, 'wb+')
        file.write(self.write_file(soup).replace('\n', os.linesep).encode(locale.getdefaultlocale()[1], errors='backslashreplace'))
        file.close()

if __name__ == '__main__':

    url = sys.argv[1]
    p = PageSaver()

    try:
        f = open("config.json")
        cfg = json.load(f)
        p.update_config(cfg)
    except Exception:
        print('Error in reading json. Applied basic template.')

    p.do_magic(url)

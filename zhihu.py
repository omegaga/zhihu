#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# -----------------------------------------
# Author: flyer <flyer103(at)gmail.com>
# Date: 2014-02-07 13:13:22
# -----------------------------------------

"""抓取知乎所有的问题，作为种子库.
"""

import sys
import time
import json
import logging

import yaml
import requests
import lxml
import lxml.html
from lxml import etree

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s][%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class ZhiHuQuestions(object):
    """Retrieve info of new questions in zhihu.
    Mainly from http://www.zhihu.com/log/questions"""
    def __init__(self):
        self.configs = self._get_configs()
        
        self.se = requests.session()
        self._init_header()

        self.login()            # 登录知乎
        self.has_login()        # 判断是否登录成功

        self.url_questions = self.configs['URL']['QUESTIONS']

        self.fp_db = open(self.configs['DB']['FILE'], 'wb')
        self.fp_except = open(self.configs['EXCEPTIONS'], 'wb')

        self.offset = 20

    def __del__(self):
        self.fp_db.close()
        self.fp_except.close()

    def _get_configs(self):
        with open('settings.yaml', 'rb') as fp:
            configs = yaml.load(fp)

        return configs

    def _init_header(self):
        self.se.headers.update(self.configs['HEADERS']['INIT'])

    def _mod_header(self):
        # may be useless
        self.se.headers.update(self.configs['HEADERS']['MOD'])

    def _get_xsrf(self):
        return self.se.cookies.get('_xsrf')

    def login(self):
        url_login = self.configs['URL']['LOGIN']        
        payload_login = {
            'email': self.configs['VALIDATE']['EMAIL'],
            'password': self.configs['VALIDATE']['PASSWORD'],
        }
        self.se.post(url_login, payload_login)

    def has_login(self):
        # !!! If the homepage of zhihu has changed, this may need to
        # be changed.
        res = self.se.get(self.configs['URL']['HOME'])
        html = etree.HTML(res.content)
        assert len(html.xpath(self.configs['NODES']['TEST'])) == 1,\
            "Failed to login or the home page doesn't has 'topic' navbar "\
            "status_code is %d" % (res.status_code,)

    def parse_json(self, string):
        res_json = json.loads(string)['msg']
        number = int(res_json[0])
        try:
            html = lxml.html.document_fromstring(res_json[1])
        except lxml.etree.XMLSyntaxError as e:
            self.fp_except.write('%s\n' % (res_json,))
            logging.error('%s' % (e.message,))
            sys.exit(-2)

        logging.info('Number of questions: %d' % (number,))

        nodes = html.xpath(self.configs['NODES']['JSON'])

        self._parse_page(nodes)

        logging.info('Done offset %d' % (self.offset,))

        last_id = int(nodes[-1].xpath('@id')[0].split('-')[-1])
        
        return last_id

    def parse_page(self, string):
        # parse the first page of http://www.zhihu.com/log/questions
        html = etree.HTML(string)
        nodes = html.xpath(self.configs['NODES']['PAGE'])

        logging.info('Number: %d' % (len(nodes),))

        self._parse_page(nodes)
        
        logging.info('Have parsed page %s' % (self.url_questions,))
        
        last_id = int(nodes[-1].xpath('@id')[0].split('-')[-1])
        
        return last_id

    def _parse_page(self, nodes):
        log = ''
        for node in nodes:
            logitem_id = int(node.xpath('@id')[0].split('-')[-1])
            
            q_title_node = node.xpath(self.configs['NODES']['TITLE'])[0]
            # url of the question
            q_title_url = '%s%s' % (self.configs['URL']['HOME'],
                                    q_title_node.xpath('@href')[0])
            # title of the question
            q_title_text = q_title_node.text
            
            q_who_node = node.xpath(self.configs['NODES']['WHO'])[0]
            # name who adds the question
            q_who_name = q_who_node.text
            try:
                # homepage of the person                
                q_who_url = '%s%s' % (self.configs['URL']['HOME'],
                                      q_who_node.xpath('@href')[0])
            except IndexError as e:
                q_who_url = ''

            # time when the questions is added
            q_time = node.xpath(self.configs['NODES']['TIME'])[0].text

            log = '%s'\
                  'Id logitem: %d\n'\
                  'Title: %s  (%s)\n'\
                  'Author: %s  (%s)\n'\
                  'Time: %s\n\n' % (log, logitem_id, q_title_text, q_title_url,
                                    q_who_name, q_who_url, q_time)
        self.fp_db.write(log.encode('utf-8'))

    def get_page(self):
        page_0 = self.se.get(self.url_questions)
        assert page_0.status_code == 200, \
            "There's something wrong when getting %s" % (self.url_questions,)
        start = self.parse_page(page_0.content)

        self._mod_header()
        while True:
            token_xsrf = self._get_xsrf()
            payload_next = {
                'start': start,
                'offset': self.offset,
                '_xsrf': token_xsrf,
            }
            
            try:
                res = self.se.post(self.url_questions, payload_next, timeout=10)
            except requests.exceptions.Timeout:
                logging.warning('Timeout')
                time.sleep(20)
                continue
            except requests.exceptions.ConnectionError:
                logging.warning('Connection Error')
                self.login()
                self.has_login()
                continue
            
            status_code = res.status_code
            logging.info('status: %d' % (status_code,))
            if status_code >= 500:
                logging.warning('status: %d' % (status_code,))
                time.sleep(10)
                continue
            elif status_code >= 400:
                msg = "Failed to get AJAX data, start %d, offset %d, status_code %d"\
                      % (start, self.offset, res.status_code)
                logging.error(msg)
                sys.exit(-1)
            start = self.parse_json(res.content)
            self.offset += 20

            time.sleep(2)
            
            
if __name__ == '__main__':
    spider = ZhiHuQuestions()
    spider.get_page()

# -*- coding: utf-8 -*-
import json
import requests
import time


instances = [
    {'ip': u'http://10.128.0.15:5000', 'name': u'i4media-sentinel1'},
    {'ip': u'http://10.128.0.16:5000', 'name': u'i4media-sentinel2'},
    {'ip': u'http://10.128.0.17:5000', 'name': u'i4media-lookup1'},
    {'ip': u'http://10.128.0.18:5000', 'name': u'i4media-lookup2'}
]

params = {
    'term': '',
#    'raw_query': '',
#    'since': '',
#    'until': '',
    'since_id': '',
    'max_id': ''
}

keywords = [
    u'#Patria', u'@AliciaCastroAR', u'@ArielSujarchuk', u'@CFKArgentina', u'@CarlosTomada', u'@CarolinaPiparo',
    u'@DiputadosFPV_pj', u'@FerEspinozaOK', u'@FernandoGray', u'@FilmusDaniel', u'@GPAlegre', u'@GafiFuks',
    u'@GugaLusto', u'@GuillermoLipera', u'@HugoYasky', u'@JPDeJesusOK', u'@JorgeFerraresi', u'@JoseCampagnoli',
    u'@Kicillofok', u'@M_Campagnoli', u'@ManesF', u'@MariaLujan_Rey', u'@MoreauLeopoldo', u'@OmarPlaini', u'@PJZurro',
    u'@PereyraJulio', u'@PrensaMadres', u'@RandazzoF', u'@RossiAgustinOK', u'@Sabbatella', u'@SantoroLeandro',
    u'@SergioBerniARG', u'@SergioMassa', u'@Stolbizer', u'@SusanaMalcorra', u'@TotyFlores', u'@WalterFesta_',
    u'@alvarezsi', u'@anibarra', u'@cambiemos', u'@ccastellanoSI', u'@danielscioli', u'@ditulliojuli',
    u'@eduardofvaldes', u'@elisacarrio', u'@estebanbullrich', u'@fernandezanibal', u'@frigeriorogelio', u'@gabicerru'
]

uri_search = 'search/tweets'
uri_timeline = 'search/timeline'


def proc_request(url, dat, t=30):
    global instances
    inst = instances
    print("-------- INSTANCES -------\n%s" % instances)
    for i in inst:
        print("Making request to %s/%s\n" % (i['ip'], url))
        print("Server name: %s" % i['name'])
        try:
            r = requests.post(
                '%s/%s' % (i['ip'], url),
                data=dat,
                timeout=t)
        except:
            print("Exception in request. Moving on...\n")
            continue
        if r.status_code == requests.codes.ok:
            print("Request Response Received\n")
            rq = r.json()
            if rq.get('error', False):
                print('Error: %s.\n' % rq.get('error'))
                print("Moving on...\n")
                continue
            print("Returning the request\n")
            return rq
    print("Instances exhausted. Waiting 5 minutes\n")
    time.sleep(300)
    return proc_request(url, dat, t)


def search_terms(keyword, max_id=None):
    global params
    global uri_search
    terms = params.copy()
    terms.update(term=keyword)
    if max_id:
        terms.update(max_id=max_id)
    ret = proc_request(uri_search, json.dumps(terms))
    if not ret:
        print('No responses for term %s\n' % keyword)
        print('Trying again in 5 minutes\n')
        time.sleep(300)
        return search_terms(keyword, max_id)
    if int(ret.get('count', 0)) > 1:
        print('%d Tweets pushed to REDIS for %s' % (ret['count'], keyword))
        with open('results.json', "w") as results:
            results.write('%s\n' % json.dumps(ret))
        if ret.get('since_id', False):
            print('Trying to get more')
            return search_terms(keyword, ret['since_id'])
        else:
            print('Done with %s' % keyword)
            return True
    else:
        print('No results found for %s' % keyword)
        if max_id:
            print('with max_id: %d\n' % max_id)
        return True
    return False


def proc_keywords():
    global keywords
    kws = keywords
    for k in kws:
        if not search_terms(k):
            print('Error en keyword: %s. Trying once more...\n' % k)
            if not search_terms(k):
                print('Too many errors for %s. Moving to next keyword' % k)
    return True


proc_keywords()
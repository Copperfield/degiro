import requests
import json
import os
from datetime import datetime
from collections import defaultdict


class Degiro:
    credentials = ['username', 'password']
    urls = {
            'login': 'https://trader.degiro.nl/login/secure/login'
    }

    def __init__(self):
        self.user = dict()
        self.data = None
        self.session = requests.Session()
        self._get_credentials()

    def _get_credentials(self):
        for credential in self.credentials:
            try:
                setattr(self, credential, os.environ[credential])
            except KeyError:
                raise KeyError(
                        f"You must to define {credential}"
                        "as enviroment variable")

    def _set_session_id(self, set_cookie):
        session_id = set_cookie
        self.session_id = session_id.split(';')[0].split('=')[1]

    def login(self):

        url = self.urls['login']
        payload = {'username': self.username,
                   'password': self.password,
                   'isPassCodeReset': False,
                   'isRedirectToMobile': False}
        header = {'content-type': 'application/json'}

        response = self.session.post(url, headers=header,
                                     data=json.dumps(payload))

        self._set_session_id(response.headers['Set-Cookie'])


    # This contain loads of user data, main interest here is the 'intAccount'
    def getConfig(self):
        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get config')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()
        self.user['intAccount'] = data['data']['intAccount']

        print('\tAccount id: {}'.format(self.user['intAccount']))

    # This gets a lot of data, orders, news, portfolio, cash funds etc.
    def getData(self):
        url = 'https://trader.degiro.nl/trading/secure/v5/update/'
        url += str(self.user['intAccount'])+';'
        url += 'jsessionid='+self.sessid
        payload = {'portfolio': 0,
                   'totalPortfolio': 0,
                   'orders': 0,
                   'historicalOrders': 0,
                   'transactions': 0,
                   'alerts': 0,
                   'cashFunds': 0,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get data')
        print('\tStatus code: {}'.format(r.status_code))

        self.data = r.json()

    # Get the cash funds
    def getCashFunds(self):
        if self.data is None:
            self.getData()
        cashFunds = dict()
        for cf in self.data['cashFunds']['value']:
            entry = dict()
            for y in cf['value']:
                # Useful if the currency code is the key to the dict
                if y['name'] == 'currencyCode':
                    key = y['value']
                    continue
                entry[y['name']] = y['value']
            cashFunds[key] = entry
        return cashFunds

    # Only returns a summary of the portfolio
    def getPortfolioSummary(self):
        pf = self.getPortfolio()
        cf = self.getCashFunds()
        tot = 0
        for eq in pf['PRODUCT'].values():
            tot += eq['value']

        pfSummary = dict()
        pfSummary['equity'] = tot
        pfSummary['cash'] = cf['EUR']['value']
        return pfSummary

    # Returns the entire portfolio
    def getPortfolio(self):
        if self.data is None:
            self.getData()
        portfolio = []
        for row in self.data['portfolio']['value']:
            entry = dict()
            for y in row['value']:
                k = y['name']
                v = None
                if 'value' in y:
                    v = y['value']
                entry[k] = v
            # Also historic equities are returned, let's omit them
            if entry['size'] != 0:
                portfolio.append(entry)

        # Restructure portfolio and add extra data
        portf_n = defaultdict(dict)
        # Restructuring
        for r in portfolio:
            pos_type = r['positionType']
            pid = r['id']  # Product ID
            del(r['positionType'])
            del(r['id'])
            portf_n[pos_type][pid] = r

        # Adding extra data
        url = 'https://trader.degiro.nl/product_search/secure/v5/products/info'
        params = {'intAccount': str(self.user['intAccount']),
                  'sessionId': self.sessid}
        header = {'content-type': 'application/json'}
        pid_list = list(portf_n['PRODUCT'].keys())
        r = self.sess.post(url,
                           headers=header,
                           params=params,
                           data=json.dumps(pid_list))
        print('\tGetting extra data')
        print('\t\tStatus code: {}'.format(r.status_code))

        for k, v in r.json()['data'].items():
            del(v['id'])
            # Some bonds tend to have a non-unit size
            portf_n['PRODUCT'][k]['size'] *= v['contractSize']
            portf_n['PRODUCT'][k].update(v)

        return portf_n

    # Returns all account transactions
    #  fromDate and toDate are strings in the format: dd/mm/yyyy
    def getAccountOverview(self, fromDate, toDate):
        url = 'https://trader.degiro.nl/reporting/secure/v4/accountoverview'
        payload = {'fromDate': fromDate,
                   'toDate': toDate,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get account overview')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()
        movs = []
        for rmov in data['data']['cashMovements']:
            mov = dict()
            # Reformat timezone part: +01:00 -> +0100
            date = ''.join(rmov['date'].rsplit(':', 1))
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
            mov['date'] = date
            mov['change'] = rmov['change']
            mov['currency'] = rmov['currency']
            mov['description'] = rmov['description']
            mov['type'] = rmov['type']
            if 'orderId' in rmov:
                mov['orderId'] = rmov['orderId']
            if 'productId' in rmov:
                mov['productId'] = rmov['productId']
            movs.append(mov)
        return movs

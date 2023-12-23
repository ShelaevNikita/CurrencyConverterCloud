#!/usr/bin/env python3

import requests

from ast import literal_eval
from pymemcache.client import base
from pymemcache.exceptions import MemcacheServerError
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from threading import Thread

from src import SpecialSymbols, CurrencyDB

class DataMining():

    URLCBR = 'https://cbr.ru/scripts/XML_daily.asp?'

    def __init__(self):
        self.currencyDictDate = {}
        self.filterKeys = [value for (_, value) in SpecialSymbols.SPECIALSYMBOLS.items()]
        self.dateNow = None
        
        self.currencyBDClass = CurrencyDB.DatabaseConverter()
        self.processDB = None

        self.memClient = base.Client('localhost:11211')
        self.timeCache = 60 * 5
       
    def getCurrencyDateURL(self, dateString):
        dataRequest = datetime.strptime(dateString, '%d-%m-%y').strftime('%d/%m/%Y')
        request = requests.get(self.URLCBR, {'date_req':dataRequest})
        soup = bs(request.content, features = 'xml')
        for tag in soup.findAll('Valute'):
            currencyValue = float(tag.find('Value').text.replace(',', '.'))
            charCode      = tag.find('CharCode').text.lower()
            self.currencyDictDate[charCode] = currencyValue
        return

    def insertCurrencyBD(self, dateString):
        dataBD = datetime.strptime(dateString, '%d-%m-%y').strftime('%Y-%m-%d')
        for key, value in self.currencyDictDate.items():
            self.currencyBDClass.insertCurrencyValue(key, value, dataBD)
        return

    def setCurrencyInMem(self, dateString):
        try:
            self.memClient.set(dateString, str(self.currencyDictDate), expire = self.timeCache)
        except MemcacheServerError:
            print(' Warning: Memcached closed...')
        return

    def setCurrencyDate(self, dateString):
        self.getCurrencyDateURL(dateString)
        self.processDB = Thread(target = self.insertCurrencyBD, 
                                args = (dateString, ), daemon = True).start()
        self.setCurrencyInMem(dateString)
        return

    def checkCurrencyInBD(self, dateString):
        dataBD = datetime.strptime(dateString, '%d-%m-%y').strftime('%Y-%m-%d')
        resultValue = self.currencyBDClass.selectCurrencyValues('rub', dataBD)       
        if resultValue is None:
            self.setCurrencyDate(dateString)
            return
        
        for key in self.filterKeys:
            resultValue = self.currencyBDClass.selectCurrencyValues(key, dataBD)
            if resultValue is not None:
                self.currencyDictDate[key] = resultValue[0]
        self.setCurrencyInMem(dateString)
        return

    def getCurrencyDate(self, dateString):
        if dateString == self.dateNow:
            return
        
        res = None
        try:
            res = self.memClient.get(dateString)
        except MemcacheServerError:
            print(' Warning: Memcached closed...')
        
        if res is not None:
            self.currencyDictDate = literal_eval(res.decode('utf-8'))
        else:
            self.checkCurrencyInBD(dateString)      
        return
    
    def makeDateArray(self, dateFrom, dateTo):
        dateArray = [dateFrom]
        date = dateFrom
        while date != dateTo:
            date = date + timedelta(days = 1)
            dateArray.append(date)
        dateArray = list(map(lambda x: x.strftime('%d-%m-%y'), dateArray))
        return dateArray

    def getCurrencyValueArray(self, currencyFrom, currencyTo, curCount, dateFrom, dateTo):
        dateArray = self.makeDateArray(dateFrom, dateTo)
        resultArray = []
        for dateString in dateArray:
            self.getCurrencyDate(dateString)
            self.dateNow = dateString
            
            currencyFromValue = self.currencyDictDate[currencyFrom]
            currencyToValue   = self.currencyDictDate[currencyTo]
            resultArray.append(round((curCount * currencyFromValue / currencyToValue), 3))
            
            if self.processDB is not None:
                self.processDB.join()
                
        return (dateArray, resultArray)

    def prepareBD(self):
        self.currencyBDClass.prepareBD()
        for key in self.filterKeys:
            self.currencyDictDate[key] = 1.0
        return

    def closeClient(self):
        self.memClient.close()
        return

    def main(self):
        self.closeClient()
        return

if __name__ == '__main__':
     DataMining().main()
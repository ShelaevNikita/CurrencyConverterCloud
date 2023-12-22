#!/usr/bin/env python3

import psycopg2

from psycopg2.extras     import execute_values
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src import SpecialSymbols

class DatabaseConverter():
    
    def __init__(self):
        self.connection  = None
        self.cursor      = None
    
    def makeConnectionWithout(self):
        try:
            self.connection = psycopg2.connect(
                user     = 'postgres',
                password = 'nikita',
                host     = 'localhost',
                port     = '5432'
            )
        except psycopg2.Error:
            print(' Error: No connection with BD...')
            return 0
        
        self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.connection.cursor()  
        return

    def closeConnection(self):
        if self.connection is not None:
            self.cursor.close()
            self.connection.close()
            self.cursor     = None
            self.connection = None
        return

    def createDatabase(self):
        if self.makeConnectionWithout() is not None:
            return 0
        createDatabaseSQL = 'CREATE DATABASE converter'    
        try:
            self.cursor.execute(createDatabaseSQL)
            self.closeConnection()
        except psycopg2.Error:
            print(' Error: No create new database...')
            return 0
        return
    
    def makeConnectionDB(self):
        try:
            self.connection = psycopg2.connect(
                user     = 'postgres',
                password = 'nikita',
                host     = 'localhost',
                port     = '5432',
                database = 'converter'
            )
        except psycopg2.Error:
            if self.createDatabase() is not None:
                return 0
            self.makeConnectionDB()
        self.cursor = self.connection.cursor()
        return

    def createTables(self):
        createTableCurrency = '''CREATE TABLE IF NOT EXISTS currency
                                 (id     SERIAL PRIMARY KEY NOT NULL,
                                  symbol VARCHAR(5) NOT NULL,
                                  name   VARCHAR(3) NOT NULL,
                                  UNIQUE (symbol, name))'''
                                  
        createTableCurValue = '''CREATE TABLE IF NOT EXISTS curValue
                                 (id     SERIAL PRIMARY KEY NOT NULL,
                                  curID  INT REFERENCES currency ON DELETE CASCADE,
                                  price  REAL NOT NULL DEFAULT 1.0 CHECK (price > 0.0),
                                  dateC  DATE NOT NULL,
                                  UNIQUE (curID, dateC))'''
        try:
            self.cursor.execute(createTableCurrency)
            self.cursor.execute(createTableCurValue)
            self.connection.commit()
            
        except psycopg2.Error:
            print(' Error: No create new tables...')
            return 0
        return

    def insertCurrency(self):
        dataCurName = [(symbol, name) for symbol, name in SpecialSymbols.SPECIALSYMBOLS.items()]
        insertCurName = 'INSERT INTO currency (symbol, name) VALUES %s ON CONFLICT (symbol, name) DO NOTHING'
        execute_values(self.cursor, insertCurName, dataCurName)
        self.connection.commit()
        return

    def prepareBD(self):
        if self.makeConnectionDB() is not None:
            return
        self.createTables()
        self.insertCurrency()
        return

    def selectCurrency(self, curName):
        selectCurrencySQL = 'SELECT id FROM currency WHERE name = %s'
        try:
            self.cursor.execute(selectCurrencySQL, (curName, ))
        except psycopg2.Error:
            print(f' Error: No currency with name "{curName}"...')
            return None
        return self.cursor.fetchone()

    def insertCurrencyValue(self, curName, value, date):
        currencyID = self.selectCurrency(curName)
        if currencyID is None:
            return
        insertCurValue = 'INSERT INTO curValue (curID, price, dateC) VALUES (%s, %s, %s)'
        try:
            self.cursor.execute(insertCurValue, (currencyID[0], value, date))
            self.connection.commit()
        except psycopg2.Error:
            print(' Error: No insert new currency value...')
            return 0
        return

    def selectCurrencyValues(self, curName, date):
        selectCurValue = '''SELECT value.price FROM curValue as value 
                            JOIN currency as cur ON cur.id = value.curID
                            WHERE (cur.name = %s AND value.dateC = %s)'''
        try:
            self.cursor.execute(selectCurValue, (curName, date))
        except psycopg2.Error:
            print(' Error: No select currency value...')
            return None
        return self.cursor.fetchone()

    def main(self):
        self.prepareBD()       
        self.closeConnection()      
        return

if __name__ == '__main__':
     DatabaseConverter().main()
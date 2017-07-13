# -*- coding: utf-8 -*-
import psycopg2 as psql
from collections import OrderedDict


class PostgreDB(object):
    __instance = None
    __host = ''
    __user = ''
    __password = ''
    __dbname = ''
    __session = None
    __connection = None

    def __init__(self, host='localhost', user='root', password='', dbname=''):
        self.__host = host
        self.__user = user
        self.__password = password
        self.__dbname = dbname

    def __open(self):
        try:
            cnx = psql.connect(dbname=self.__dbname, host=self.__host,
                user=self.__user, password=self.__password)
            self.__connection = cnx
            self.__session = cnx.cursor()
        except psql.Error as e:
            print(("Error %d: %s" % (e.args[0], e.args[1])))

    def __close(self):
        self.__session.close()
        self.__connection.close()
    ## End def __close

    def select(self, table, where=None, *args, **kwargs):
        result = None
        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        l = len(keys) - 1

        for i, key in enumerate(keys):
            query += " " + key + " "
            if i < l:
                query += ","
        ## End for keys

        query += 'FROM %s' % table

        if where:
            query += " WHERE %s" % where
        ## End if where

        self.__open()
        self.__session.execute(query, values)
        number_rows = self.__session.rowcount
        number_columns = len(self.__session.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.__session.fetchall()]
        else:
            result = [item[0] for item in self.__session.fetchall()]
        self.__close()

        return result
    ## End def select

    def update(self, table, where=None, *args, **kwargs):
        query = "UPDATE %s SET " % table
        keys = list(kwargs.keys())
        values = tuple(kwargs.values()) + tuple(args)
        l = len(keys) - 1
        for i, key in enumerate(keys):
            query += "`" + key + "` = %s"
            if i < l:
                query += ","
            ## End if i less than 1
        ## End for keys
        query += " WHERE %s" % where

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()

        # Obtain rows affected
        update_rows = self.__session.rowcount
        self.__close()

        return update_rows
    ## End function update

    def insert(self, table, *args, **kwargs):
        values = None
        query = "INSERT INTO %s " % table
        if kwargs:
            keys = list(kwargs.keys())
            values = tuple(kwargs.values())
            query += "(" + ",".join(["%s"] * len(keys)) % tuple(keys)
            query += ") VALUES (" + ",".join(["%s"] * len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"] * len(values)) + ")"

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()
        self.__close()
        return self.__session.lastrowid
    ## End def insert

    def delete(self, table, where=None, *args):
        query = "DELETE FROM %s" % table
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()

        # Obtain rows affected
        delete_rows = self.__session.rowcount
        self.__close()

        return delete_rows
    ## End def delete

    def select_advanced(self, sql, *args):
        od = OrderedDict(args)
        query = sql
        values = tuple(od.values())
        self.__open()
        self.__session.execute(query, values)
        number_rows = self.__session.rowcount
        number_columns = len(self.__session.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.__session.fetchall()]
        else:
            result = [item[0] for item in self.__session.fetchall()]

        self.__close()
        return result
    ## End def select_advanced
## End class
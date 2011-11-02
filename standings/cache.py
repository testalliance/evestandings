from hashlib import sha1
import logging
import sqlite3

SQLITE_PATH = '/tmp/eveapicache.sqlite3'

class DbCacheHandler:
    """
    Database backed cache handler for Entity's eveapi module
    """

    def __init__(self, conn=SQLITE_PATH):
        self._conn_url = conn

    @property
    def log(self):
        if not hasattr(self, '_log'):
            self._log = logging.getLogger(self.__class__.__name__)
        return self._log

    @property
    def conn(self):
        if not hasattr(self, '_conn') or not self._conn:
            self._conn = sqlite3.connect(self._conn_url)
            self.setup()
        return self._conn

    @property
    def cursor(self):
        if not hasattr(self, '_cursor') or not self._cursor:
            self._cursor = self.conn.cursor()
        return self._cursor

    def setup(self):
        if not hasattr(self, '_setupchecked'):
            self.cursor.execute('CREATE TABLE IF NOT EXISTS api_cache(docid TEXT PRIMARY KEY, xml TEXT, cacheduntil TEXT)')
            self._setupchecked = True

    def disconnect(self):
        if hasattr(self, '_cursor'):
            self._cursor.close()
            self._cursor = None
        if hasattr(self, '_conn'):
            self._conn.close()
            self._conn = None

    @staticmethod
    def _gen_docid(host, path, params):
        return sha1("%s%s?%s" % (host, path, params)).hexdigest()

    def retrieve(self, host, path, params):
        docid = self._gen_docid(host, path, params)
        self.log.debug("Retrieving document: %s" % docid)
        try:
            self.cursor.execute("SELECT xml FROM api_cache WHERE docid = ? and datetime(cacheduntil, 'unixepoch') >= current_timestamp", (docid,))
            res = self.cursor.fetchone()
            self.disconnect()
        except sqlite3.Error as e:
            self.log.error("Error retrieving document: %s", e.args[0])
        else:
            if res:
                self.log.debug("Found %s documents for ID %s" % (len(res), docid))
                return res[0]
        return None

    def store(self, host, path, params, doc, obj):
        docid = self._gen_docid(host, path, params)
        self.log.debug("Storing document: %s (%s)" % (docid, path))
        try:
            self.cursor.execute('REPLACE INTO api_cache (docid, xml, cacheduntil) VALUES (?, ?, ?)', (docid, doc, obj.cachedUntil))
            self.conn.commit()
            self.disconnect()
        except sqlite3.Error as e:
            self.log.error("Error storing document: %s", e.args[0])

    def purge_stale(self):
        self.log.info("Purging stale cached documents")
        try:
            self.cursor.execute("DELETE FROM api_cache WHERE datetime(cacheduntil, 'unixepoch') >= current_timestamp")
            self.conn.commit()
            self.disconnect()
        except sqlite3.Error as e:
            self.log.error("Error purging document cache: %s", e.args[0])

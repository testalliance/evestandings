# -*- coding: utf-8 -*-

import sys
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from eveapi import EVEAPIConnection, Error
from jinja2 import Environment, PackageLoader

from standings.cache import DbCacheHandler

__version__ = '0.1'

STANDINGS_ALLIANCE = 0
STANDINGS_CORPORATION = 1

class Standings:
    """
    Grabs the latest Standings from the EVE API and outputs them into
    a nice template format
    """

    def __init__(self, keyid, vcode, characterid, dbpath='/tmp/standingscache.sqlite3', type=STANDINGS_ALLIANCE):
        self.eveapi = EVEAPIConnection(cacheHandler=DbCacheHandler(dbpath)).auth(keyID=keyid, vCode=vcode)
        self.character = characterid
        self.standings_type = type

    @property
    def _get_alliance_id_list(self):
        if not hasattr(self, '_allianceids'):
            self._allianceids = set([x.allianceID for x in EVEAPIConnection().eve.AllianceList().alliances])
        return self._allianceids

    def _check_if_corp(self, corpid):
        try:
            res = EVEAPIConnection().corp.CorporationSheet(corporationID=corpid)
        except Error:
            return False
        return True

    def _get_standings(self):
        res = self.eveapi.corp.ContactList(characterID=self.character)

        standings = OrderedDict()
        for x in ['excellent', 'good', 'neutral', 'bad', 'terrible']: standings[x] = []

        def parse_list(list, output):
            for row in list:
                level = float(row['standing'])
                if level > 5 and level <= 10:
                    type = 'excellent'
                elif level > 0 and level <= 5:
                    type = 'good'
                elif level < 0 and level >= -5:
                    type = 'bad'
                elif level < -5 and level >= -10:
                    type = 'terrible'
                else:
                    # Neutral?
                    type = 'neutral'

                if int(row['contactID']) in self._get_alliance_id_list:
                    rowtype = 'alli'
                elif self._check_if_corp(int(row['contactID'])):
                    rowtype = 'corp'
                else:
                    rowtype = 'char'

                output[type].append((rowtype, row['contactID'], row['contactName'], row['standing']))

            # Order standings for each group
            for x in ['excellent', 'good', 'neutral', 'bad', 'terrible']:
                standings[x] = sorted(standings[x], key=lambda v: -int(v[3]))


        if self.standings_type == STANDINGS_ALLIANCE:
            parse_list(res.allianceContactList, standings)
        else:
            parse_list(res.corporateContactList, standings)

        return standings

    def _get_name(self):
        res = self.eveapi.corp.CorporationSheet()
        if hasattr(res, 'allianceName'): return res.allianceName
        return res.corporationName

    def _get_html(self, template='standings_list.html'):
        if not template: template = 'standings_list.html'
        env = Environment(loader=PackageLoader('standings', 'templates'))
        template = env.get_template(template)
        return template.render(standings=self._get_standings(), name=self._get_name())

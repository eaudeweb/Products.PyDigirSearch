# -*- coding: utf-8 -*-
try:
    import json
except ImportError:
    import simplejson as json

from datetime import datetime
from urllib2 import urlopen
from urllib import urlencode
import time
import urllib

from OFS.SimpleItem import SimpleItem
from App.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from naaya.core.paginator import DiggPaginator, EmptyPage, InvalidPage
from naaya.core.utils import force_to_unicode
from Products.NaayaCore.GeoMapTool.managers.kml_gen import kml_generator

from MySQLConnector import MySQLConnector

manage_add_html = PageTemplateFile('zpt/manage_add', globals())
def manage_add_search(self, id, REQUEST=None):
    """ Create new PyDigirSearch object from ZMI.
    """
    ob = PyDigirSearch(id)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)
    return ob

from Products.NaayaCore.LayoutTool.DiskFile import allow_path
allow_path('Products.PyDigirSearch:www/css/')

QUERY_TERMS = {
    'InstitutionCode': 'equals',
    'CollectionCode': 'equals',
    'BasisOfRecord': 'equals',
    'Family': 'equals',
    'Genus': 'like',
    'Species': 'like',
    'Country': 'like',
    'Locality': 'like',
    }


class PyDigirSearch(SimpleItem):
    """
        PyDigirSearch object
    """
    meta_type = 'Search DiGIR Provider'
    security = ClassSecurityInfo()

    items_per_page = 20

    manage_options = (
        SimpleItem.manage_options
        +
        (
            {'label' : 'Properties', 'action' :'manage_edit_html'},
        )
    )

    def __init__(self, id):
        """
            Constructor that builds new PyDigirSearch object.
        """
        self.id = id
        self.access_point = 'http://localhost:8080/DigirProvider'
        self.host_name = 'http://localhost:8080'
        self.mysql_connection = {}
        self.mysql_connection['host'] = 'localhost'
        self.mysql_connection['name'] = 'repository'
        self.mysql_connection['user'] = 'cornel'
        self.mysql_connection['pass'] = 'cornel'
        self.solr_connection = 'http://localhost:8983/solr'

    _index_html = PageTemplateFile('zpt/index', globals())
    security.declareProtected(view, 'index_html')
    def index_html(self, REQUEST=None):
        """ """
        if not self.get_solr_status():
            self.setSessionErrorsTrans('Error accessing solr server')
        return self._index_html()

    security.declareProtected(view, 'metadata_html')
    metadata_html = PageTemplateFile('zpt/metadata', globals())

    security.declareProtected(view, 'results_html')
    results_html = PageTemplateFile('zpt/results', globals())

    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/PyDigirSearch_manage_edit', globals())

    security.declareProtected(view_management_screens, 'manageProperties')
    def manageProperties(self, REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG

        if REQUEST is not None:
            params = dict(REQUEST.form)
        else:
            params = kwargs
        access_point = params.pop('access_point')
        self.access_point = access_point
        host_name = params.pop('host_name')
        self.host_name = host_name
        self.mysql_connection = {}
        self.mysql_connection['host'] = params.pop('mysql_host')
        self.mysql_connection['name'] = params.pop('mysql_name')
        self.mysql_connection['user'] = params.pop('mysql_user')
        self.mysql_connection['pass'] = params.pop('mysql_pass')

        self.solr_connection = params.pop('solr_connection')

        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok')

    def open_dbconnection(self):
        """ Create and return a MySQL connection object """
        conn = MySQLConnector()
        conn.open(self.mysql_connection['host'], self.mysql_connection['name'],
                  self.mysql_connection['user'], self.mysql_connection['pass'])
        return conn

    def str2date(self, date_string):
        return datetime(*(time.strptime(date_string, '%d/%m/%Y')[0:3]))

    def quote_value(self, s):
        """ """
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        return urllib.quote(s)

	security.declarePrivate('get_solr_status')
    def get_solr_status(self):
        """ """
        try:
            conn = urlopen('%s/dataimport?command=status&wt=json' % self.solr_connection)
            result = json.load(conn)
            return result['responseHeader']['status'] == 0
        except:
            return False

    security.declareProtected(view, 'get_field_results')
    def get_field_results(self, query, searched_field, query_field=None):
        """ """
        if query_field is None:
            query_field = searched_field

        query = {'q': '%s:%s*' % (query_field, query.lower()),
                'fq': 'entity_type:%s' % searched_field,
                'wt': 'json',
                'rows': 100}

        url = u"%s/select/?%s" % (self.solr_connection, urlencode(query))
        conn = urlopen(url)

        result = json.load(conn)
        return [r[searched_field] for r in result['response']['docs']]

    security.declareProtected(view, 'get_json')
    def get_json(self, REQUEST=None, query='', searched_field='Family', query_field=None):
        """ """
        records = self.get_field_results(query, searched_field, query_field)
        records = [{"name": r} for r in records]
        return json.dumps(records)

    security.declarePrivate('get_query_string')
    def get_query_string(self, request):
        query_items = []

        for qt, qv in request.SESSION.items():
            if qt == 'filter_by_InstitutionCode':
                query_filters = 'InstitutionCode: (%s)' % ' OR '.join('"%s"' % v for v in qv.split('++'))
                query_items.append(query_filters)

            if qt == 'filter_by_CollectionCode':
                query_filters = 'CollectionCode: (%s)' % ' OR '.join('"%s"' % v for v in qv.split('++'))
                query_items.append(query_filters)

            if qv and qt in QUERY_TERMS:
                if QUERY_TERMS[qt] == 'equals':
                    query_items.append('%s:"%s"' % (qt, qv))
                elif QUERY_TERMS[qt] == 'like':
                    query_items.append('%s:"%s"' % (qt, qv))

        start_year = request.SESSION.get('CollectionDateStartYear')
        start_month = request.SESSION.get('CollectionDateStartMonth')
        start_day = request.SESSION.get('CollectionDateStartDay')
        if not start_year:
            start_year = 1750
            start_month = 1
            start_day = 1
        elif not start_month:
            start_month = 1
            start_day = 1
        elif not start_day:
            start_day = 1

        end_year = request.SESSION.get('CollectionDateEndYear')
        end_month = request.SESSION.get('CollectionDateEndMonth')
        end_day = request.SESSION.get('CollectionDateEndDay')
        if not end_year:
            end_year = datetime.now().year + 100
            end_month = 12
            end_day = 31
        elif not end_month:
            end_month = 12
            end_day = 31
        elif not end_day:
            end_day = 31

        year_range = '{%s TO %s}' % (start_year, end_year)
        start_month_range = '{%s TO 13}' % start_month
        start_day_range = '[%s TO 31]' % start_day
        end_month_range = '{-1 TO %s}' % end_month
        end_day_range = '[0 TO %s]' % end_day
        date_query_items = ['YearCollected:%s' % year_range,
                '(YearCollected:%s AND MonthCollected:%s)' % (start_year, start_month_range),
                '(YearCollected:%s AND MonthCollected:%s AND DayCollected:%s)' % (start_year, start_month, start_day_range),
                '(YearCollected:%s AND MonthCollected:%s)' % (end_year, end_month_range),
                '(YearCollected:%s AND MonthCollected:%s AND DayCollected:%s)' % (end_year, end_month, end_day_range),
                ]
        if request.SESSION.get('AllResults'):
            date_query_items.append('YearCollected:0')

        date_query_string = '(%s)' % (' OR '.join(date_query_items))
        query_items.append(date_query_string)

        return ' AND '.join(query_items).encode('utf-8')

    security.declareProtected(view, 'metadata')
    def metadata(self, REQUEST):
        """ """
        if REQUEST.REQUEST_METHOD == 'POST':
            REQUEST.SESSION.clear()
            for qt in QUERY_TERMS.keys():
                if REQUEST.get(qt):
                    self.setSession(qt, REQUEST.get(qt))

            start_year = REQUEST.get('CollectionDateStartYear')
            if start_year:
                self.setSession('CollectionDateStartYear', start_year)
            start_month = REQUEST.get('CollectionDateStartMonth')
            if start_month:
                self.setSession('CollectionDateStartMonth', start_month)
            start_day = REQUEST.get('CollectionDateStartDay')
            if start_day:
                self.setSession('CollectionDateStartDay', start_day)

            end_year = REQUEST.get('CollectionDateEndYear')
            if end_year:
                self.setSession('CollectionDateEndYear', end_year)
            end_month = REQUEST.get('CollectionDateEndMonth')
            if end_month:
                self.setSession('CollectionDateEndMonth', end_month)
            end_day = REQUEST.get('CollectionDateEndDay')
            if end_day:
                self.setSession('CollectionDateEndDay', end_day)

            if REQUEST.get('AllResults'):
                self.setSession('AllResults', REQUEST.get('AllResults'))

        institutions, collections = self.get_metadata(REQUEST)

        return self.metadata_html(REQUEST, institutions=institutions, collections=collections)

    security.declarePrivate('get_metadata')
    def get_metadata(self, request):
        def get_results(filter):
            ret = {}
            for i, r in enumerate(filter):
                if i % 2 == 0:
                    key = r
                else:
                    ret[key] = r
            return ret

        query = [('q', self.get_query_string(request)),
                    ('rows', 0),
                    ('facet', 'on'),
                    ('facet.field', 'CollectionCode'),
                    ('facet.field', 'InstitutionCode'),
                    ('facet.mincount', 1),
                    ('wt', 'json')]

        url = "%s/select/?%s" % (self.solr_connection, urlencode(query))
        conn = urlopen(url)
        filters = json.load(conn)['facet_counts']['facet_fields']

        return (get_results(filters['InstitutionCode']),
                get_results(filters['CollectionCode']))

    security.declareProtected(view, 'search')
    def search(self, REQUEST):
        """ """
        #put filters on session
        institutions = REQUEST.form.get('institution', [])
        if not isinstance(institutions, list):
            institutions = [institutions]

        if institutions:
            self.setSession('filter_by_InstitutionCode', '++'.join(institutions))

        collections = REQUEST.form.get('collection', [])
        if not isinstance(collections, list):
            collections = [collections]

        if collections:
            self.setSession('filter_by_CollectionCode', '++'.join(collections))

        records, records_found = self.search_database(rows = self.items_per_page,
                                                      request = REQUEST)
        return self.results_html(REQUEST,
                                 records = records,
                                 fake_records = range(int(records_found)))

    security.declarePrivate('search_database')
    def search_database(self, rows, request):
        """ """
        query_string = self.get_query_string(request)
        sort_on = request.get('sort', 'CollectionCode asc')

        try:
            page = int(request.get('page', '1'))
        except ValueError:
            page = 1

        query = {'q': query_string,
                'sort': sort_on,
                'rows': rows,
                'start':  (page-1)*self.items_per_page,
                'wt': 'json'}

        url = "%s/select/?%s" % (self.solr_connection, urlencode(query))
        conn = urlopen(url)
        result = json.load(conn)
        return result['response']['docs'], result['response']['numFound']

    security.declareProtected(view, 'record_details_html')
    record_details_html = PageTemplateFile('zpt/record_details', globals())

    security.declareProtected(view, 'get_record_details')
    def get_record_details(self, id):
        """ get record details """
        dbconn = self.open_dbconnection()
        result = dbconn.query(u"""
                SELECT darwin_collectioncode AS CollectionCode,
                      darwin_institutioncode AS InstitutionCode,
                      darwin_catalognumber as CatalogNumber,
                      darwin_scientificname AS ScientificName,
                      darwin_basisofrecord AS BasisOfRecord,
                      darwin_kingdom AS Kingdom,
                      darwin_phylum AS Phylum,
                      darwin_class AS Class,
                      darwin_order AS `Order`,
                      darwin_family AS Family,
                      darwin_genus AS Genus,
                      darwin_species AS Species,
                      darwin_subspecies AS Subspecies,
                      darwin_scientificnameauthor AS ScientificNameAuthor,
                      darwin_typestatus AS TypeStatus,
                      darwin_collector AS Collector,
                      darwin_yearcollected AS YearCollected,
                      darwin_monthcollected AS MonthCollected,
                      darwin_daycollected AS DayCollected,
                      darwin_continentocean AS ContinentOcean,
                      darwin_country AS Country,
                      darwin_county AS County,
                      darwin_locality AS Locality,
                      darwin_longitude AS Longitude,
                      darwin_latitude AS Latitude,
                      darwin_sex AS Sex,
                      darwin_notes AS Notes
                  FROM darwin
                  WHERE record_id=%s""" % id)
        dbconn.close()
        if result:
            return result[0]

    security.declareProtected(view, 'download_kml')
    def download_kml(self, REQUEST):
        """ """

        output = []
        out_app = output.append

        kml = kml_generator()
        out_app(kml.header())
        out_app(kml.style())

        records, records_found = self.search_database(rows=1000, request=REQUEST)
        for record in records:
                out_app(kml.add_point(self.utToUtf8(record['id']),
                                      self.utXmlEncode(record.get('ScientificName', '')),
                                      self.utXmlEncode(record.get('Notes', '')),
                                      '%s/misc_/PyDigirSearch/marker.png' % self.absolute_url(),
                                      self.utToUtf8(record.get('Longitude', '')),
                                      self.utToUtf8(record.get('Latitude', '')),
                                      self.utToUtf8('%s, %s' %
                                                    (record.get('Family', ''),
                                                     record.get('Genus', ''))
                                                   ),
                                      self.absolute_url(),
                                      self.absolute_url(),
                                      '%s/details?id=%s' % (self.absolute_url(),
                                                            record['id']),
                                      self.utXmlEncode('%s, %s' %
                                                       (record.get('Locality', ''),
                                                       (record.get('Country', ''))))
                                        )
                        )

        out_app(kml.footer())
        REQUEST.RESPONSE.setHeader('Content-Type', 'application/vnd.google-earth.kml+xml')
        REQUEST.RESPONSE.setHeader('Content-Disposition', 'attachment;filename=records.kml')
        return '\n'.join(output)

    security.declareProtected(view, 'details')
    details = PageTemplateFile('zpt/details', globals())

InitializeClass(PyDigirSearch)
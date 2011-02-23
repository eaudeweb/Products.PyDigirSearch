from OFS.SimpleItem import SimpleItem
from App.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from naaya.core.paginator import DiggPaginator, EmptyPage, InvalidPage

try:
    import json
except ImportError:
    import simplejson as json

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

items_per_page = 10

QUERY_TERMS = {
    'InstitutionCode': 'equals',
    'CollectionCode': 'equals',
    # 'BasisOfRecord': 'equals',
    'Family': 'equals',
    'Genus': 'like',
    'Species': 'like',
    'ScientificName': 'like',
    # 'Country': 'equals',
    'Locality': 'like',
    }

class PyDigirSearch(SimpleItem):
    """
        PyDigirSearch object
    """
    meta_type = 'Search DiGIR Provider'
    security = ClassSecurityInfo()

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

    security.declareProtected(view, 'index_html')
    index_html = PageTemplateFile('zpt/index', globals())
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

        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok')

    def open_dbconnection(self):
        """ Create and return a MySQL connection object """
        conn = MySQLConnector()
        conn.open(self.mysql_connection['host'], self.mysql_connection['name'],
                  self.mysql_connection['user'], self.mysql_connection['pass'])
        return conn

    security.declareProtected(view, 'search')
    def search(self, REQUEST):
        """ """
        dbconn = self.open_dbconnection()

        for qt in QUERY_TERMS.keys():
            self.setSession(qt, REQUEST.get(qt, REQUEST.SESSION.get(qt)))

        records, match_count = self.search_database(dbconn, REQUEST)
        dbconn.close()
        all_records = [number for number in range(int(match_count[0].get('counter')))]
        pages = self.itemsPaginator(all_records, REQUEST)

        return self.results_html(REQUEST, records=records, pages=pages)

    def itemsPaginator(self, records, REQUEST):
        """ """
        paginator = DiggPaginator(records, items_per_page, body=5, padding=2, orphans=0)   #Show 10 documents per page

        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(REQUEST.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            items = paginator.page(page)
        except (EmptyPage, InvalidPage):
            items = paginator.page(paginator.num_pages)

        return items

    security.declareProtected(view, 'get_institutions')
    def get_institutions(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_institutioncode AS InstitutionCode
                                FROM darwin
                                WHERE darwin.darwin_institutioncode LIKE "%s%%"
                                ORDER BY InstitutionCode LIMIT 100""" % query)

    security.declareProtected(view, 'get_collections')
    def get_collections(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_collectioncode AS CollectionCode
                                FROM darwin
                                WHERE darwin.darwin_collectioncode LIKE "%s%%"
                                ORDER BY CollectionCode LIMIT 100""" % query)

    security.declareProtected(view, 'get_countries')
    def get_countries(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_country AS Country
                                FROM darwin
                                WHERE darwin.darwin_country LIKE "%s%%"
                                ORDER BY Country LIMIT 100""" % query)

    security.declareProtected(view, 'get_basisofrecords')
    def get_basisofrecords(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_basisofrecord AS BasisOfRecord
                                FROM darwin
                                WHERE darwin.darwin_basisofrecord LIKE "%s%%"
                                ORDER BY BasisOfRecord""" % query)

    security.declareProtected(view, 'get_genres')
    def get_genres(self, family, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_genus AS Genus
                                FROM darwin
                                WHERE darwin.darwin_family = "%s"
                                ORDER BY Genus""" % family)

    security.declareProtected(view, 'get_species')
    def get_species(self, genus, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_species AS Species
                                FROM darwin
                                WHERE darwin.darwin_genus = "%s"
                                ORDER BY Species""" % genus)

    security.declareProtected(view, 'get_names')
    def get_names(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_scientificnameauthor AS ScientificNameAuthor
                                FROM darwin
                                WHERE darwin.darwin_scientificnameauthor LIKE "%s%%"
                                ORDER BY ScientificNameAuthor LIMIT 100""" % query)

    security.declareProtected(view, 'get_countries')
    def get_countries(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_country AS Country
                                FROM darwin
                                WHERE darwin.darwin_country LIKE "%s%%"
                                ORDER BY Country LIMIT 100""" % query)

    security.declareProtected(view, 'get_localities')
    def get_localities(self, query, dbconn):
        """ """
        return dbconn.query(u"""SELECT DISTINCT darwin.darwin_locality AS Locality
                                FROM darwin
                                WHERE darwin.darwin_locality LIKE "%s%%"
                                ORDER BY Locality LIMIT 100""" % query)

    def test_sql(self):
        """ """
        sql = u"""select darwin_locality from darwin where darwin_collectioncode = 'Baraniak'"""
        dbconn = self.open_dbconnection()
        res = dbconn.query(sql)
        return res[0]['darwin_locality']

    security.declareProtected(view, 'get_json')
    def get_json(self, REQUEST=None, type='families', value=None):
        """ """
        dbconn = self.open_dbconnection()

        records = {}
        if type == 'institutions':
            records = self.get_institutions(value, dbconn)
        elif type == 'collections':
            records = self.get_collections(value, dbconn)
        elif type == 'basisofrecords':
            records = self.get_basisofrecords(value, dbconn)
        elif type == 'families':
            records = self.get_families(value, dbconn)
        elif type == 'genus':
            records = self.get_genres(value, dbconn)
        elif type == 'species':
            records = self.get_species(value, dbconn)
        elif type == 'countries':
            records = self.get_countries(value, dbconn)
        elif type == 'localities':
            records = self.get_localities(value, dbconn)
        elif type == 'names':
            records = self.get_names(value, dbconn)
        dbconn.close()
        return json.dumps(records)

    security.declarePrivate('search_database')
    def search_database(self, dbconn, request):

        sort_pieces = request.get('skey', 'CollectionCode').split('_')
        if len(sort_pieces) > 1:
            sort_order = 'DESC'
        else:
            sort_order = 'ASC'
        sort_on = 'darwin.darwin_%s' % sort_pieces[0].lower()

        try:
            page = int(request.get('page', '1'))
        except ValueError:
            page = 1
        start = (page-1)*items_per_page

        query_terms = [ qt for qt, qv in request.SESSION.items() if qv ]
        if query_terms:
            sql_condition = 'WHERE '
        else:
            sql_condition = ''

        for qt in query_terms:
            if QUERY_TERMS[qt] == 'equals':
                sql_condition += u"%s = '%s'" % ('darwin.darwin_%s' % qt.lower(), request.SESSION.get(qt))
            elif QUERY_TERMS[qt] == 'like':
                sql_condition += u"%s LIKE '%s%%'" % ('darwin.darwin_%s' % qt.lower(), request.SESSION.get(qt))
            if query_terms.index(qt) < len(query_terms)-1:
                sql_condition += u" AND "

        sql = u"""SELECT darwin.darwin_collectioncode AS CollectionCode,
                        darwin.darwin_institutioncode AS InstitutionCode,
                        darwin.darwin_scientificname AS ScientificName,
                        darwin.darwin_basisofrecord AS BasisOfRecord,
                        darwin.darwin_kingdom AS Kingdom,
                        darwin.darwin_phylum AS Phylum,
                        darwin.darwin_class AS Class,
                        darwin.darwin_order AS `Order`,
                        darwin.darwin_family AS Family,
                        darwin.darwin_genus AS Genus,
                        darwin.darwin_species AS Species,
                        darwin.darwin_subspecies AS Subspecies,
                        darwin.darwin_scientificnameauthor AS ScientificNameAuthor,
                        darwin.darwin_typestatus AS TypeStatus,
                        darwin.darwin_collector AS Collector,
                        darwin.darwin_yearcollected AS YearCollected,
                        darwin.darwin_monthcollected AS MonthCollected,
                        darwin.darwin_daycollected AS DayCollected,
                        darwin.darwin_continentocean AS ContinentOcean,
                        darwin.darwin_country AS Country,
                        darwin.darwin_county AS County,
                        darwin.darwin_locality AS Locality,
                        darwin.darwin_longitude AS Longitude,
                        darwin.darwin_latitude AS Latitude,
                        darwin.darwin_sex AS Sex,
                        darwin.darwin_notes AS Notes
                FROM record
                INNER JOIN document ON record.document_id = document.document_id
                INNER JOIN folder ON document.folder_id = folder.folder_id
                INNER JOIN resource ON folder.resource_id = resource.resource_id
                LEFT JOIN darwin ON record.record_id = darwin.record_id %s
                ORDER BY %s %s LIMIT %s OFFSET %s""" % (sql_condition, sort_on, sort_order, items_per_page, start)
        records = dbconn.query(sql)

        sql = u"""SELECT count(record.record_id) AS counter
                FROM record
                INNER JOIN document ON record.document_id = document.document_id
                INNER JOIN folder ON document.folder_id = folder.folder_id
                INNER JOIN resource ON folder.resource_id = resource.resource_id
                LEFT JOIN darwin ON record.record_id = darwin.record_id %s""" % sql_condition
        match_count = dbconn.query(sql)

        return records, match_count

InitializeClass(PyDigirSearch)

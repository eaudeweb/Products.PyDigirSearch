import re
import os
from os.path import join, dirname, splitext
import urllib

from lxml import etree, objectify

from App.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from naaya.core.paginator import DiggPaginator, EmptyPage, InvalidPage

from OFS.SimpleItem import SimpleItem

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

class PyDigirSearch(SimpleItem):
    """
        PyDigirSearch object
    """
    meta_type = 'Search DiGIR Provider'
    security = ClassSecurityInfo()

    def __init__(self, id):
        """
            Constructor that builds new PyDigirSearch object.
        """
        self.id = id

    security.declareProtected(view, 'index_html')
    index_html = PageTemplateFile('zpt/index', globals())
    security.declareProtected(view, 'results_html')
    results_html = PageTemplateFile('zpt/results', globals())

    security.declareProtected(view, 'search')
    def search(self, REQUEST):
        """ """
        self.setSession('CollectionCode',
            REQUEST.get('CollectionCode', REQUEST.SESSION.get('CollectionCode')))
        self.setSession('Family',
            REQUEST.get('Family', REQUEST.SESSION.get('Family')))
        self.setSession('Genus',
            REQUEST.get('Genus', REQUEST.SESSION.get('Genus')))
        self.setSession('Species',
            REQUEST.get('Species', REQUEST.SESSION.get('Species')))
        self.setSession('ScientificNameAuthor',
            REQUEST.get('ScientificNameAuthor', REQUEST.SESSION.get('ScientificNameAuthor')))
        self.setSession('Country',
            REQUEST.get('Country', REQUEST.SESSION.get('Country')))
        self.setSession('Locality',
            REQUEST.get('Locality', REQUEST.SESSION.get('Locality')))
        self.setSession('skey',
            REQUEST.get('skey', REQUEST.SESSION.get('skey', 'CollectionCode')))
        self.setSession('page',
            REQUEST.get('page', REQUEST.SESSION.get('page', '1')))
        response = self.make_request(REQUEST)
        records, match_count, record_count, end_of_records = self.parse_response(response)
        all_records = [number for number in range(int(match_count))]
        pages = self.itemsPaginator(all_records, REQUEST)

        return self.results_html(REQUEST, records=records, pages=pages)

    def itemsPaginator(self, records, REQUEST):
        """ """
        paginator = DiggPaginator(records, items_per_page, body=5, padding=2, orphans=5)   #Show 10 documents per page

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

    security.declarePrivate('get_response')
    def parse_response(self, response):
        """ """
        results = etree.fromstring(response)
        ns = {
            'xmlns': 'http://digir.net/schema/protocol/2003/1.0',
            'darwin': 'http://digir.net/schema/conceptual/darwin/2003/1.0',
        }

        records = []
        for record in results.xpath('xmlns:content/xmlns:record', namespaces=ns):
            record_data = {}
            for child in record.getchildren():
                record_data.setdefault(child.tag.replace('{%s}' % ns['darwin'], ''), child.text)
            records.append(record_data)

        diagnostics = results.xpath('xmlns:diagnostics', namespaces=ns)[0]
        match_count = diagnostics.xpath('xmlns:diagnostic[@code="MATCH_COUNT"]', namespaces=ns)[0].text
        record_count = diagnostics.xpath('xmlns:diagnostic[@code="RECORD_COUNT"]', namespaces=ns)[0].text
        end_of_records = diagnostics.xpath('xmlns:diagnostic[@code="END_OF_RECORDS"]', namespaces=ns)[0].text

        return records, match_count, record_count, end_of_records

    security.declarePrivate('make_request')
    def make_request(self, params):
        """ """
        xml = self.build_xml(params)

        sort_pieces = params.SESSION.get('skey').split('_')
        if len(sort_pieces) > 1:
            sort_order = 'DESC'
        else:
            sort_order = 'ASC'
        sort_on = 'darwin.darwin_%s' % sort_pieces[0].lower()

        params = urllib.urlencode({'doc': xml, 'sort_on':sort_on, 'sort_order':sort_order})
        opener = urllib.FancyURLopener({})
        f = opener.open('http://localhost:8080/DigirProvider/', params)
        response = f.read()
        f.close()
        return response

    security.declarePrivate('build_xml')
    def build_xml(self, params):
        """ """
        xmlns = "http://digir.net/schema/protocol/2003/1.0"
        xsd = "http://www.w3.org/2001/XMLSchema"
        darwin = "http://digir.net/schema/conceptual/darwin/2003/1.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "%s %s %s %s" % ('http://digir.net/schema/protocol/2003/1.0',
                                        'http://digir.sourceforge.net/schema/protocol/2003/1.0/digir.xsd',
                                        'http://digir.net/schema/conceptual/darwin/2003/1.0',
                                        'http://digir.sourceforge.net/schema/conceptual/darwin/2003/1.0/darwin2.xsd')

        root = etree.Element("{"+xmlns+"}request", attrib={"{" + xsi + "}schemaLocation" : schemaLocation}, 
                                nsmap={'xsi':xsi, None:xmlns, 'xsd':xsd, 'darwin':darwin})

        #buid header
        header = etree.SubElement(root, "header")
        version = etree.SubElement(header, "version")
        version.text = '1.0.0'
        sendTime = etree.SubElement(header, "sendTime")
        sendTime.text = '2003-06-05T11:57:00-03:00'
        source = etree.SubElement(header, "source")
        source.text = 'http://localhost:8080'
        destination = etree.SubElement(header, "destination", resource="rsr27f332f85e2d9136fee6e1b28988702d")
        destination.text = 'http://localhost:8080/DigirProvider/'
        type = etree.SubElement(header, "type",)
        type.text = 'search'

        #build search
        search = etree.SubElement(root, "search")
        filter = etree.SubElement(search, "filter")

        #build filters
        and_operator = etree.SubElement(filter, "and")
        equals = etree.SubElement(and_operator, "equals")
        collectioncode = etree.SubElement(equals, "{http://digir.net/schema/conceptual/darwin/2003/1.0}CollectionCode")
        collectioncode.text = params.SESSION.get('CollectionCode', '')

        like = etree.SubElement(and_operator, "like")
        family = etree.SubElement(like, "{http://digir.net/schema/conceptual/darwin/2003/1.0}Family")
        family.text = params.SESSION.get('Family', '')

        #build records
        try:
            page = int(params.SESSION.get('page', '1'))
        except ValueError:
            page = 1

        start = str((page-1)*items_per_page)
        records = etree.SubElement(search, "records", limit=str(items_per_page), start=start)
        structure = etree.SubElement(records, "structure", schemaLocation="http://digir.sourceforge.net/schema/conceptual/darwin/full/2003/1.0/darwin2full.xsd")
        count = etree.SubElement(search, "count")
        count.text = "true"
        return (etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True))

InitializeClass(PyDigirSearch)
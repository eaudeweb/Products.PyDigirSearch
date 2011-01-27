import re
import os
from os.path import join, dirname, splitext
import urllib
from xml.sax.saxutils import escape

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

QUERY_TERMS = {
    'CollectionCode': 'equals',
    'Family': 'like',
    'Genus': 'like',
    'Species': 'like',
    'ScientificNameAuthor': 'like',
    'Country': 'equals',
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

        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok')

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
        #self.setSession('skey',
        #    REQUEST.get('skey', REQUEST.SESSION.get('skey', 'CollectionCode')))
        #self.setSession('page',
        #    REQUEST.get('page', REQUEST.SESSION.get('page', '1')))
        response = self.make_request(REQUEST)
        records, match_count, record_count, end_of_records = self.parse_response(response)
        all_records = [number for number in range(int(match_count))]
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

    security.declarePrivate('get_response')
    def parse_response(self, response):
        """ parse DiGIR response """
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
        """ make a request to DiGIR provider """
        xml = self.build_xml(params)

        sort_pieces = params.get('skey', 'CollectionCode').split('_')
        if len(sort_pieces) > 1:
            sort_order = 'DESC'
        else:
            sort_order = 'ASC'
        sort_on = 'darwin.darwin_%s' % sort_pieces[0].lower()

        params = urllib.urlencode({'doc': xml, 'sort_on':sort_on, 'sort_order':sort_order})
        opener = urllib.FancyURLopener({})
        f = opener.open(self.access_point, params)
        response = f.read()
        f.close()
        return response

    security.declarePrivate('build_xml')
    def build_xml(self, params):
        """ build the request xml """
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

        #build header
        header = etree.SubElement(root, "header")
        version = etree.SubElement(header, "version")
        version.text = '1.0.0'
        sendTime = etree.SubElement(header, "sendTime")
        sendTime.text = '2003-06-05T11:57:00-03:00'
        source = etree.SubElement(header, "source")
        source.text = self.host_name
        destination = etree.SubElement(header, "destination", resource="rsr27f332f85e2d9136fee6e1b28988702d")
        destination.text = self.access_point
        type = etree.SubElement(header, "type",)
        type.text = "search"

        #build search
        search = etree.SubElement(root, "search")
        filter = etree.SubElement(search, "filter")

        #build filters
        filters_container = self.build_filters(params)
        filter.append(filters_container.getchildren()[0])

        #build records
        try:
            page = int(params.get('page', '1'))
        except ValueError:
            page = 1

        start = str((page-1)*items_per_page)
        records = etree.SubElement(search, "records", limit=str(items_per_page), start=start)
        structure = etree.SubElement(records, "structure", schemaLocation="http://digir.sourceforge.net/schema/conceptual/darwin/full/2003/1.0/darwin2full.xsd")
        count = etree.SubElement(search, "count")
        count.text = "true"
        return (etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True))

    security.declarePrivate('join_filters')
    def join_filters(self, node1, node2, params):
        if node1 in QUERY_TERMS.keys():
            node1_value = "<darwin:%s>%s</darwin:%s>" % (node1, escape(params.SESSION.get(node1)), node1)
            node1_condition = "<%s>%s</%s>" % (QUERY_TERMS[node1], node1_value, QUERY_TERMS[node1])
        else:
            node1_condition = node1
        node2_value = "<darwin:%s>%s</darwin:%s>" % (node2, escape(params.SESSION.get(node2)), node2)
        node2_condition = "<%s>%s</%s>" % (QUERY_TERMS[node2], node2_value, QUERY_TERMS[node2])
        return "<and>%s%s</and>" % (node1_condition, node2_condition)

    security.declarePrivate('build_filters')
    def build_filters(self, params):
        qnames = [ k for k,v in params.SESSION.items() if v ]
        if qnames:
            partial = qnames[0]
            if len(qnames) > 2:
                for name in qnames[1:]:
                    partial = self.join_filters(partial, name, params)
            else:
                partial_value = "<darwin:%s>%s</darwin:%s>" % (partial, escape(params.SESSION.get(partial)), partial)
                partial = "<%s>%s</%s>" % (QUERY_TERMS[partial], partial_value, QUERY_TERMS[partial])
        else:
            partial = "<like><darwin:CollectionCode></darwin:CollectionCode></like>"    #DiGIR request at least one condition
        # namespace prefix darwin must be defined otherwise lxml will failed to parse this xml
        # we define the darwin namespace on a dummy container
        xml = "<request xmlns='http://digir.net/schema/protocol/2003/1.0' xmlns:darwin='http://digir.net/schema/conceptual/darwin/2003/1.0'>" + partial + "</request>"
        return etree.fromstring(xml)

InitializeClass(PyDigirSearch)
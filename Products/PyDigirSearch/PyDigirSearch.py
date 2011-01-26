import re
import os
from os.path import join, dirname, splitext
import urllib

from lxml import etree, objectify

from App.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

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
        response = self.make_request()
        records, match_count, record_count, end_of_records = self.parse_response(response)

        return self.results_html(REQUEST, objects=records)

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
    def make_request(self):
        """ """
        xml = self.build_xml()
        params = urllib.urlencode({'doc': xml})
        opener = urllib.FancyURLopener({})
        f = opener.open('http://localhost:8080/DigirProvider/', params)
        response = f.read()
        f.close()
        return response

    security.declarePrivate('build_xml')
    def build_xml(self):
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
        equals = etree.SubElement(filter, "equals")
        collectioncode = etree.SubElement(equals, "{http://digir.net/schema/conceptual/darwin/2003/1.0}CollectionCode")
        collectioncode.text = "Svampefund2006"

        #build records
        records = etree.SubElement(search, "records", limit="10", start="0")
        structure = etree.SubElement(records, "structure", schemaLocation="http://digir.sourceforge.net/schema/conceptual/darwin/full/2003/1.0/darwin2full.xsd")
        count = etree.SubElement(search, "count")
        count.text = "true"
        return (etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True))

InitializeClass(PyDigirSearch)
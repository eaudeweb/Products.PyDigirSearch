import PyDigirSearch
from App.ImageFile import ImageFile

def initialize(context):
    """
        Product initialization method
        @param context: Zope server context
    """
    context.registerClass(
        PyDigirSearch.PyDigirSearch,
        constructors = (
            PyDigirSearch.manage_add_html,
            PyDigirSearch.manage_add_search),
        icon = 'www/meta_type.png'
    )

misc_ = {
    'digir_search_style.css':ImageFile('www/css/digir_search_style.css', globals()),
    'search_digir.js':ImageFile('www/js/search_digir.js', globals()),
    'arrows.gif':ImageFile('www/arrows.gif', globals()),
    's.gif':ImageFile('www/s.gif', globals()),
    'marker.png':ImageFile('www/marker.png', globals()),
}
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
    )

#misc_ = {
#    'search_digir.js':ImageFile('www/js/search_digir.js', globals()),
#}
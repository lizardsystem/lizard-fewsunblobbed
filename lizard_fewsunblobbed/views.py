from django.shortcuts import render_to_response
from lizard_fewsunblobbed.models import Filter

def fews_browser(request):    
    tree = Filter.dump_bulk()    
    return render_to_response('filter_tree.html', 
                              {"tree": tree})


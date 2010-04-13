from django.shortcuts import render_to_response
from django.template import RequestContext
from lizard_fewsunblobbed.models import Filter

def fews_filter_tree(request, template='lizard_fewsunblobbed/filter_tree.html'):    
    tree = Filter.dump_bulk()    
    return render_to_response(template,
                              {"tree": tree},
                              context_instance=RequestContext(request))


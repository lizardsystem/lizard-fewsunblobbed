from django.shortcuts import render_to_response
from django.template import RequestContext
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie

def fews_filter_tree(request, template='lizard_fewsunblobbed/filter_tree.html'):    
    tree = Filter.dump_bulk()    
    return render_to_response(template,
                              {"tree": tree},
                              context_instance=RequestContext(request))

def fews_parameter_tree(request, filterkey=90, locationkey=37551, template='lizard_fewsunblobbed/parameter_tree.html'):
    filtered_timeseries = Timeserie.objects.filter(filterkey=filterkey, locationkey=locationkey)
    parameters = [ts.parameterkey for ts in filtered_timeseries]
    return render_to_response(template,
                             {"parameters": parameters},
                              context_instance=RequestContext(request))


    

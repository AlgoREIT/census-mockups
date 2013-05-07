from __future__ import division
import collections
from importd import d
import simplejson as pyjson
from math import ceil
import requests

d(INSTALLED_APPS=["django.contrib.humanize"])

# Hit Ian's gist for now
API_ENDPOINT = 'https://gist.github.com/iandees/0dc098ac27d20b456058/raw/a3dd6b2f6f3df19bf6ad56c339268cc7923aa66a/cook_county.json'

@d("/")
def index(request):
    return d.HttpResponse("hello world")

@d("/profile/")
def profile(request):
    # hit the API and store the results for later operations
    r = requests.get(API_ENDPOINT)
    data = pyjson.loads(r.text, object_pairs_hook=collections.OrderedDict)

    # initial page context
    page_context = data

    # add some max values and ratios
    total_population = data['population']['total']
    page_context['population']['age_gender_max'] = get_max_value(dict(data['population']['gender']))
    page_context['education']['attainment_max'] = get_max_value(dict(data['education']['attainment']))
    page_context['insurance']['insurance_max'] = get_max_value(dict(data['insurance']))
    page_context['language_max'] = get_max_value(dict(data['language']))
    
    page_context['insurance']['percent_with_no_insurance'] = get_ratio(
        data['insurance']['No Insurance'], total_population
    )

    # to the template!
    return "geography.html", page_context


## A little generator to pluck out max values ##

def drill(item):
    if isinstance(item, int) or isinstance(item, float):
        yield item
    elif isinstance(item, list):
        for i in item:
            for result in drill(i):
                yield result
    elif isinstance(item, dict):
        for k,v in item.items():
            for result in drill(v):
                yield result

def get_max_value(nested_dicts):
    max_value = max([item for item in drill(nested_dicts)])
    return max_value

def get_ratio(num1, num2):
    return round(num1 / num2, 2)*100

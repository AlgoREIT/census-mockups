from __future__ import division
import collections
from numpy import median
import simplejson as pyjson
import requests

from importd import d
from math import ceil
from random import randint

d(INSTALLED_APPS=["django.contrib.humanize"])


@d("/")
def index(request):
    return d.HttpResponse("hello world")

@d("/profile/")
def view(request):
    # Hit Ian's gist for now
    API_ENDPOINT = 'https://gist.github.com/iandees/0dc098ac27d20b456058/raw/a3dd6b2f6f3df19bf6ad56c339268cc7923aa66a/cook_county.json'
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
    return "profile.html", page_context


@d("/compare/<slug:state_code>/counties/json/", name="compare_json")
def json(request, state_code=None):
    state_code = state_code.upper()
    page_context = {
        'state_code': state_code,
        'geography_type': 'counties',
    }

    # hit the API and store the results for later operations
    API_ENDPOINT = API_ENDPOINTS[state_code]
    r = requests.get(API_ENDPOINT)
    data = pyjson.loads(r.text, object_pairs_hook=collections.OrderedDict)

    data_groups = collections.OrderedDict()
    for geo in data:
        name = geo['geography']['name']
        geoID = geo['geography']['geoid'].split('US')[1]
        total_population = geo['population']['total']

        for group, values in geo['population']['gender'].items():
            group_name_total = '%s total' % group
            group_name_pct = '%s percentage' % group

            if not group_name_total in data_groups:
                data_groups[group_name_pct] = {}
                data_groups[group_name_total] = {}

            data_groups[group_name_pct].update({
                geoID: round((values['total'] / total_population)*100,1),
            })
            data_groups[group_name_total].update({
                geoID: values['total'],
            })

    return data_groups

API_ENDPOINTS = {
    'IL': 'https://gist.github.com/iandees/eedbb8ab3caa31bfdb25/raw/4ff31fcd6192318df61961a6674e873b5b9f96d3/illinois_compare.json',
    'FL': 'https://gist.github.com/iandees/eedbb8ab3caa31bfdb25/raw/de8c95ec49e0ede7ef9dc505bcb67e7300595041/florida_compare.json',
    'WA': 'https://gist.github.com/iandees/eedbb8ab3caa31bfdb25/raw/330722d4bffe99b1ac6f6827bd65c27e2fde550c/washington_compare.json',
}

@d("/compare/<slug:state_code>/counties/<slug:compare_type>/", name="compare")
def view(request, state_code=None, compare_type='distribution'):
    template_name = 'compare_%s.html' % compare_type
    state_code = state_code.upper()
    page_context = {
        'state_code': state_code,
        'geography_type': 'counties',
    }

    # hit the API and store the results for later operations
    API_ENDPOINT = API_ENDPOINTS[state_code]
    r = requests.get(API_ENDPOINT)
    data = pyjson.loads(r.text, object_pairs_hook=collections.OrderedDict)

    if compare_type == 'table':
        geo_values = []
        for geo in data:
            name = geo['geography']['name']
            geoID = geo['geography']['geoid']
            total_population = geo['population']['total']
            geo_item = {
                'name': name,
                'geoID': geoID,
                'total_population': total_population,
                'values': collections.OrderedDict(),
            }
            for group, values in geo['population']['gender'].items():
                geo_item['values'].update({
                    group: {
                        'male': values['male'],
                        'male_pct': round((values['male'] / values['total'])*100,1),
                        'female': values['female'],
                        'female_pct': round((values['female'] / values['total'])*100,1),
                        'total': values['total'],
                        'total_pct': round((values['total'] / total_population)*100,1),
                    }
                })
            geo_values.append(geo_item)
        
        page_context.update({
            'geo_values': geo_values,
        })

        
    elif compare_type == 'distribution' or 'map':
        coal_charts = collections.OrderedDict()
        for geo in data:
            name = geo['geography']['name']
            geoID = geo['geography']['geoid']
            total_population = geo['population']['total']
            for group, values in geo['population']['gender'].items():
                if not group in coal_charts:
                    coal_charts[group] = {
                        'group_baselines': {},
                        'group_values': {},
                    }
                coal_charts[group]['group_values'].update({
                    geoID: {
                        'name': name,
                        'male': values['male'],
                        'male_pct': round((values['male'] / values['total'])*100,1),
                        'female': values['female'],
                        'female_pct': round((values['female'] / values['total'])*100,1),
                        'total': values['total'],
                        'total_pct': round((values['total'] / total_population)*100,1),
                    }
                })

        for chart, chart_values in coal_charts.items():
            for field in ['total', 'total_pct']:
                values_list = [value[field] for geo, value in chart_values['group_values'].items()]
                max_value = max(values_list)
                min_value = min(values_list)
                domain_range = max_value - min_value
                median_value = int(median(values_list))
                median_percent_of_range = ((median_value - min_value) / domain_range)*100
                chart_values['group_baselines']['max_value_%s' % field] = max_value
                chart_values['group_baselines']['min_value_%s' % field] = min_value
                chart_values['group_baselines']['domain_range_%s' % field] = domain_range
                chart_values['group_baselines']['median_value_%s' % field] = median_value
                chart_values['group_baselines']['median_percent_of_range_%s' % field] = round(median_percent_of_range,1)
                for geo, value in chart_values['group_values'].items():
                    percentage = ((value[field] - min_value) / domain_range)*100
                    value['percent_of_range_%s' % field] = round(percentage,1)

        geography_list = sorted([(geo, value['name']) for geo, value in chart_values['group_values'].items()])
        
        page_context.update({
            'coal_charts': coal_charts,
            'geography_list': geography_list,
            'api_endpoint': API_ENDPOINT,
        })
        
    return template_name, page_context



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
    
'''
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


@d("/comparison/")
def comparison(request):
    page_context = {}

    # create our random data
    category_headers = [
        'Category A',
        'Category B',
        'Category C',
        'Category D',
        'Category E',
    ]
    category_values = {}
    for header in category_headers:
        header_values = [None] * 100
        for index, value in enumerate(header_values):
            header_values[index] = randint(500,10000)
        category_values[header] = header_values

    # now pack it into a dict of geographies, like we'd get from an API call
    category_header_values = [category_values[category] for category in category_headers]
    category_max_values = [max(l) for l in category_header_values]
    geo_list = []
    for index, (a, b, c, d, e) in enumerate(zip(*category_header_values)):
        values_list = [a, b, c, d, e]
        total = sum(values_list)
        values = []
        for i, value in enumerate(values_list):
            percentage = (value/total)*100
            max_value = category_max_values[i]
            max_ratio = (value/max_value)*100
            values.append({
                'value': value,
                'percentage': '{0:.1f}'.format(percentage),
                'max_ratio': '{0:.1f}'.format(max_ratio),
            })
        
        geo = {
            'name': 'Geography %s' % (index + 1),
            'values': values,
            'total': total
        }
        geo_list.append(geo)
        
    print geo_list
        
    # now take results of our "API call," and break them into chartable lists
    line_plots = []
    for header in category_headers:
        line_plots.append({
            'group_name': header,
            'group_values': []
        })
    
    for index, geo in enumerate(geo_list):
        for i, value in enumerate(geo_list[index]['values']):
            geo = {
                'name': geo['name'],
                'value': value['value']
            }
            line_plots[i]['group_values'].append(geo)

    for plot in line_plots:
        values_list = [geo['value'] for geo in plot['group_values']]
        max_value = max(values_list)
        min_value = min(values_list)
        domain_range = max_value - min_value
        median_value = int(median(values_list))
        median_percent_of_range = ((median_value - min_value) / domain_range) * 100
        plot['max_value'] = max_value
        plot['min_value'] = min_value
        plot['domain_range'] = domain_range
        plot['median_value'] = median_value
        plot['median_percent_of_range'] = '{0:.1f}'.format(median_percent_of_range)
        for geo in plot['group_values']:
            percentage = ((geo['value'] - min_value) / domain_range) * 100
            geo['percent_of_range'] = '{0:.1f}'.format(percentage)
            
    page_context.update({
        'category_headers': category_headers,
        'geo_values': geo_list,
        'coal_charts': coal_charts,
        'comparison_number': len(header_values)
    })
    return "comparison.html", page_context
    
county_values = [None] * 30
for index, value in enumerate(county_values):
    values = []
    random_values = [
        randint(500,10000),
        randint(500,10000),
        randint(500,10000),
        randint(500,10000),
        randint(500,10000),
    ]
    total = sum(random_values)
    total_min = min(random_values)
    total_max = max(random_values)

    values = []
    for value in random_values:
        max_ratio = (value/total_max)*100
        percentage = (value/total)*100
        values.append({'value': value, 'max_ratio': max_ratio, 'percentage': percentage})
        
    county = {
        'name': 'County %s' % (index + 1),
        'values': values,
        'total': total
    }
    county_values[index] = county
'''

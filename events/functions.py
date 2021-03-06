import urllib2
import json
import re
from models import Event, Category, Rating, RatingValue, Weight
from FBGraph.Graph import Graph
from FBGraph.models import User
from app_config import GOKERA_API, WEIGHT_WEBSITE_TEXT, WEIGHT_DESCRIPTION_TEXT, WEIGHT_CATEGORY, \
    WEIGHT_CATEGORY_NAME, WEIGHT_DESCRIPTION_NAME, WEIGHT_WEBSITE_NAME
from django.core.exceptions import ObjectDoesNotExist


def create_urls(begin, end):
    """
    Generate all the available url for the API to fetch the event
    Return : List with all the urls
    """
    url_template = GOKERA_API

    out = list()
    for i in range(begin, end+1):
        out.append(url_template % i)
    return out


def fetch__update_database():
    """
    Fetch & Update the database.
    Return : tuple (categoriesUpdated, categoriesInserted, eventsUpdated, eventsInserted)
    """
    categories_updated = list()
    categories_inserted = list()
    events_updated = list()
    events_inserted = list()

    for u in create_urls(1, json.load(urllib2.urlopen(create_urls(1, 1)[0]))['totalPages']):
        for e in json.load(urllib2.urlopen(u))['events']:
            cat = None
            try:
                cat = Category.objects.get(external_id=e['category']['objectId'])

                if cat.name != e['category']['name']:
                    cat.name = e['category']['name']
                    categories_updated.append(cat.name)
            except ObjectDoesNotExist:
                cat = Category(external_id=e['category']['objectId'], name=e['category']['name'])
                categories_inserted.append(cat.name)
            cat.save()  # NOT THREAD-SAFE !

            event = None
            description = re.sub('\\n', ' ', e['description'])
            try:
                event = Event.objects.get(external_id=e['objectId'])
                if unicode(event.category.external_id) != e['category']['objectId'] \
                    or unicode(event.external_id) != e['objectId'] \
                    or unicode(event.name) != e['name'] \
                    or unicode(event.website) != e['website'] \
                    or unicode(event.description) != description:

                    event.category = cat
                    event.external_id = e['objectId']
                    event.name = e['name']
                    event.website = e['website']
                    event.description = description
                    events_updated.append(event.name)

            except ObjectDoesNotExist:
                event = Event(category=cat,
                              external_id=e['objectId'],
                              name=e['name'],
                              website=e['website'],
                              description=description)

                events_inserted.append(event.name)

            event.save()  # NOT THREAD-SAFE !

    update_weight_database()
    return categories_updated, categories_inserted, events_updated, events_inserted


def update_weight_database():
    for k, v in {WEIGHT_CATEGORY_NAME: WEIGHT_CATEGORY,
                 WEIGHT_DESCRIPTION_NAME: WEIGHT_DESCRIPTION_TEXT,
                 WEIGHT_WEBSITE_NAME: WEIGHT_WEBSITE_TEXT}.items():
        Weight(name=k, weight=v).save()


def get_all_categories():
    """
    Return all the existing categories in the fetch__update_database
    Return : List of Category objects
    """
    return Category.objects.all().order_by('name')


def add_event_process(post):
    """
    Add the event past by POST method.
    Return : event's unicode
    """
    cat = Category.objects.get(external_id=post['category'])
    e = Event(category=cat,
              external_id=post['external_id'],
              name=post['name'],
              description=post['description'],
              website=post['website']
              )
    e.save()
    return e.__unicode__()


def get_all_event_sorted(token):
    """
    Get all the events in a dictionary : Rated and Unrated according to the user. For the rated events,
    you'll have if the current user likes or dislikes
    Return : Dictionary {rated, unrated}
    rated : List[List of Event object, Like or Dislike]
    unrated : List[List of Event objects]
    """
    current_user = User.objects.get(external_id=Graph(token).get_me()['id'])

    rated_events = list()
    for r in Rating.objects.filter(user=current_user):
        rated_events.append([Event.objects.get(id=r.event.id), r.rating])
    unrated_events = Event.objects.exclude(id__in=[r[0].id for r in rated_events])

    return {'rated': rated_events,
            'unrated': unrated_events}


def rate_event_process(external_id, rating, token):
    """
    Insert, Update or delete the event
    """
    if int(rating) < 0:
        try:
            Rating.objects.get(event=Event.objects.get(external_id=external_id)).delete()
        except ObjectDoesNotExist:
            #  The value doesn't exist, so it's already deleted
            pass
    else:
        e = Event.objects.get(external_id=external_id)
        u = User.objects.get(external_id=Graph(token).get_me()['id'])
        r = None
        try:
            r = Rating.objects.get(event=e, user=u)
            r.rating = rating
        except ObjectDoesNotExist:
            r = Rating(event=e, user=u, rating=rating)
        r.save()



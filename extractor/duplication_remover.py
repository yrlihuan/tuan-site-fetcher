import logging
import extractor

def process(data, siteid):
    """
    Some sites keep multiple entries for the same item, because
    the item is sold in different cities.
    This module removes the duplication and combine the cities
    in the result GrouponInfo
    """
    if not isinstance(data, list) or \
       not isinstance(data[0], extractor.GrouponInfo):
        logging.error('Dup_remover: the input is not an array')
        return None

    groupon_dict = {}
    for groupon in data:
        title = groupon.title
        if title not in groupon_dict:
            groupon_dict[title] = groupon
        else:
            old_entity = groupon_dict[title]
            city = groupon.city
            if city not in old_entity.city:
                old_entity.city += ',' + city

    return groupon_dict.values()


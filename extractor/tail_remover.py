import logging
import extractor

def process(data, siteid, tail):
    """
    Remove unnecessary url params from groupon links
    """
    if not isinstance(data, list) or \
       not isinstance(data[0], extractor.GrouponInfo):
        logging.error('Tail_remover: the input is not an array')
        return None

    for groupon in data:
        if groupon.url.endswith(tail):
            p = groupon.url.rfind(tail)
            groupon.url = groupon.url[0:p]

    return data

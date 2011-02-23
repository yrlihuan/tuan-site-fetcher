def validate_site_name(site):
    domain_surfix = '.appspot.com'

    if domain_surfix in site:
        return site

    if '.' not in site:
        return site + domain_surfix


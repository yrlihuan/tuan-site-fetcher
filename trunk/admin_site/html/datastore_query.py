STYLE = u"""
<style>
p {
max-width: 500px;
overflow: hidden;
white-space: nowrap;
text-overflow: ellipsis;
}
</style>
"""

TABLE = u"""
<body>
    <table>
        <tbody>
            %s
            %s
        </tbody>
    </table>
</body>
"""


TABLE_ROW = u"""
            <tr>
                %s
            </tr>
"""

HEADER_ITEM = u'''
<th align="left">
    <p>
    %s
    </p>
</th>
'''

CELL_ITEM = u'''
<td>
    <p>
    %s
    </p>
</td>
'''

LINK_ITEM = u'''
<td>
    <p>
        <a href="%s">%s</a>
    </p>
</td>
'''

DISPLAYS = ['url', 'title', 'original', 'current', \
            'discount', 'bought', 'shop', 'address', \
            'cpu_usage', 'outgoing_bandwidth', 'incomming_bandwidth', \
            'siteid', 'updateserver', 'error', 'sites', 'servertype']

LINKABLE = ['url']

def get_html(data, server='', table=''):
    if len(data) == 0:
        return ''

    props = vars(data[0]).keys()

    # generate table header
    header_items = ''
    for prop in props:
        if prop in DISPLAYS:
            header_items += HEADER_ITEM % prop

    header_row = TABLE_ROW % header_items

    # generate table items
    data_rows = ''
    for d in data:
        data_items = ''
        for prop in props:
            if prop not in DISPLAYS:
                continue
            
            if prop in LINKABLE:
                value = getattr(d, prop)
                link = '/datastore/display?server=%s&table=%s&field=%s&value=%s' % (server, table, prop, value)
                data_items += LINK_ITEM % (unicode(link), unicode(value))
            else:
                data_items += CELL_ITEM % unicode(getattr(d, prop))

        data_rows += TABLE_ROW % data_items

    return STYLE + (TABLE % (header_row, data_rows))



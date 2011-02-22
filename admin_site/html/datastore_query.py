STYLE = u"""
<style>
p {
max-width: 200px;
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

def get_html(data):
    if len(data) == 0:
        return ''

    props = vars(data[0]).keys()

    # generate table header
    header_items = ''
    for prop in props:
        header_items += HEADER_ITEM % prop

    header_row = TABLE_ROW % header_items

    # generate table items
    data_rows = ''
    for d in data:
        data_items = ''
        for prop in props:
            data_items += CELL_ITEM % unicode(getattr(d, prop))

        data_rows += TABLE_ROW % data_items

    return STYLE + (TABLE % (header_row, data_rows))



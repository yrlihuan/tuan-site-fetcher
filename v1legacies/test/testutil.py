import logging
import traceback

def run_test(test, verbose=False, **args):
    print '-' * 60
    print 'Starting test ' + test.func_name

    try:
        result = test(**args)
    except Exception, ex:
        trace = traceback.format_exc()
        logging.error(trace)
        result = False

    if result:
        print 'Succeed! ' + test.func_name
    else:
        print 'Failed! ' + test.func_name

    if verbose:
        print result

    print 'Test ended ' + test.func_name

def assert_eq(value, expected):
    if value != expected:
        raise Exception('Value: %s, Expected: %s' % (str(value), str(expected)))


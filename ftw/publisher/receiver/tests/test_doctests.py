from Testing import ZopeTestCase as ztc
from ftw.publisher.receiver.tests.base import ReceiverTestCase
import doctest
import unittest


OPTIONFLAGS = (doctest.NORMALIZE_WHITESPACE|
               doctest.ELLIPSIS|
               doctest.REPORT_NDIFF)

INTEGRATION_TESTS = [
    'decoder.txt',
    'receive.txt',
    ]

def test_suite():
    return unittest.TestSuite([
            # doctests in file bar.txt
            ztc.ZopeDocFileSuite(
                filename,
                test_class=ReceiverTestCase, optionflags=OPTIONFLAGS)

            for filename in INTEGRATION_TESTS])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

from Products.ZWiki.testsupport import *
#ZopeTestCase.installProduct('ZCatalog')
ZopeTestCase.installProduct('ZWiki')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Tests))
    return suite

class Tests(ZwikiTestCase):

    def test_PageTypeRst(self):
        self.p.edit(text='! PageOne PageTwo\n',type='rst')
        self.assertEquals(
            self.p.render(bare=1),
            '<blockquote>\nPageOne PageTwo</blockquote>\n<p>\n</p>\n')

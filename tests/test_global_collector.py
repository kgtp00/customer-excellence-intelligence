import unittest
from collect_global import extract, canonical_url, run

class TestGlobalDiscovery(unittest.TestCase):
    def test_across_extracts_one(self):
        sample = '''<nav><a href="/resources/expert-insights/">Expert Insights</a></nav>
        <article><a href="/resources/expert-insights/segmented-hcp-engagement/">Segmented HCP engagement and AI transformation</a></article>'''
        rows = extract('Across Health', 'https://across.health/resources/expert-insights/', ('/resources/expert-insights/',), sample)
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]['topics'])
        self.assertIsNone(rows[0]['publication_date'])
    def test_reject_external_and_generic_links(self):
        sample = '''<a href="https://external.example/articles/1">Big competitor study on AI</a>
        <a href="/resources/expert-insights/">Read more</a>
        <a href="/resources/expert-insights/actual-study/">Read more</a>'''
        rows = extract('Across Health', 'https://across.health/resources/expert-insights/', ('/resources/expert-insights/',), sample)
        self.assertEqual(len(rows),0)
    def test_zs_internal_canonicalization(self):
        url=canonical_url('/content/zs/en/insights/pharma-marketing-future', 'https://www.zs.com/industry-insights/pharmaceuticals-biotech')
        self.assertEqual(url,'https://www.zs.com/insights/pharma-marketing-future')
    def test_failures_isolated(self):
        html='''<a href="/resources/expert-insights/omnichannel-success-study/">Research on customer omnichannel transformation</a>'''
        def f(url):
            if 'across.health' in url: return html.encode(), 'utf-8'
            raise ConnectionError('cannot reach')
        output=run(fetch=f,allow=lambda url:(True,'test'))
        self.assertEqual(output['total_candidates'],1)
        self.assertEqual(len(output['source_checks']),7)
        self.assertEqual(len([x for x in output['source_checks'] if x['status']=='failed']),6)

if __name__ == '__main__': unittest.main()

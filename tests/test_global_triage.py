import unittest
from triage_global import triage, make_report

def sample(title,source="Across Health",url="https://across.health/resources/expert-insights/x"):
    return {"title":title,"source":source,"url":url}
class TriageTests(unittest.TestCase):
    def test_strong(self):
        self.assertEqual(triage(sample("Omnichannel strategy for pharma"))["editorial_queue"],"priority_editorial_review")
    def test_zs_slug_requires_verification(self):
        r=triage(sample("/content/zs/en/insights/modernizing-gtm-and-customer-experience-with-ai","ZS","https://www.zs.com/insights/modernizing-gtm-and-customer-experience-with-ai"))
        self.assertEqual(r["title_status"],"url_slug_placeholder_needs_verification")
        self.assertNotIn("/content/zs/",r["title"])
    def test_veeva_prefix(self):
        r=triage(sample("Industry Report Read Report Veeva Agentic Commercial Trends Report","Veeva","https://www.veeva.com/resources/agentic-commercial-trends-report"))
        self.assertEqual(r["title"],"Veeva Agentic Commercial Trends Report")
        self.assertEqual(r["editorial_queue"],"priority_editorial_review")
    def test_off_scope(self):
        r=triage(sample("Press Release Read Press Release Veeva DQS Cleans Data for Clinical Trials","Veeva","https://www.veeva.com/resources/data"))
        self.assertEqual(r["editorial_queue"],"off_scope_archive")
    def test_no_auto_publication(self):
        r=triage(sample("HCP customer experience benchmarks"))
        self.assertFalse(r["auto_publish"])
        self.assertIsNone(r["publication_date"])
    def test_totals(self):
        out=make_report({"collected_at":"2026-10-27","records":[sample("Omnichannel engagement"),sample("Clinical trials and drug discovery")]})
        self.assertEqual(sum(out["queue_totals"].values()),2)
if __name__=="__main__":unittest.main()

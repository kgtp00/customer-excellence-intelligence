import unittest
from publish_discoveries import build
class FeedTests(unittest.TestCase):
    def test_prior_date_preserved_and_slug_skipped(self):
        sample={"records":[{"url":"https://www.example.org/a","title":"Omnichannel in pharmaceutical marketing","source":"Example","topics":["Content & Omnichannel"],"editorial_queue":"priority_editorial_review","title_status":"source_anchor_text"},{"url":"https://www.example.org/b","title":"unverified-slug-title-from-url","source":"Example","editorial_queue":"priority_editorial_review","title_status":"url_slug_placeholder_needs_verification"}]}
        prior={"items":[{"url":"https://www.example.org/a","first_seen":"2026-10-20"}]}
        d=build(sample,prior,"2026-10-27")
        self.assertEqual(len(d["items"]),1)
        self.assertEqual(d["items"][0]["first_seen"],"2026-10-20")
        self.assertIsNone(d["items"][0]["publication_date"])
    def test_no_unapproved_abstracts(self):
        d=build({"records":[{"url":"https://www.example.org/a","title":"AI and commercial transformation study","source":"Example","editorial_queue":"priority_editorial_review","title_status":"source_anchor_text","finding":"unverified claim"}]})
        self.assertNotIn("finding",d["items"][0])
    def test_low_relevance_excluded(self):
        d=build({"records":[{"url":"https://www.example.org/a","title":"Clinical research workflow and database","editorial_queue":"off_scope_archive","title_status":"source_anchor_text"}]})
        self.assertEqual(len(d["items"]),0)
if __name__=="__main__":unittest.main()

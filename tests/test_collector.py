import datetime as dt
import unittest
from collect_govuk import classify, build

TODAY = dt.date(2026, 10, 27)

def r(title, date="2026-10-10", suffix=None):
    return {"title": title, "description": title, "link": f"/government/news/{suffix or len(title)}", "public_timestamp": date}

class TestCollector(unittest.TestCase):
    def test_ai_detects_standalone_ai(self):
        doc = classify(r("National Commission into the Regulation of AI in Healthcare"), today=TODAY)
        self.assertTrue(doc["ai"])
        self.assertEqual(doc["triage"], "priority_review")

    def test_not_ai_inside_words(self):
        doc = classify(r("Fair claims and advertising"), today=TODAY)
        self.assertFalse(doc["ai"])

    def test_marketing_authorisation_is_not_commercial_marketing(self):
        doc = classify(r("Medicines: apply for a variation to your marketing authorisation"), today=TODAY)
        self.assertEqual(doc["triage"], "archive_low_relevance")

    def test_routine_approval_archived(self):
        doc = classify(r("MHRA authorises product for adults"), today=TODAY)
        self.assertEqual(doc["triage"], "archive_low_relevance")

    def test_promotion_flagged(self):
        doc = classify(r("Advertising investigations: September 2026"), today=TODAY)
        self.assertEqual(doc["triage"], "priority_review")

    def test_older_relevant_item_archive(self):
        doc = classify(r("Advertising investigations: January 2026", "2026-02-12"), today=TODAY)
        self.assertEqual(doc["triage"], "archive_older")

    def test_future_rejected(self):
        self.assertIsNone(classify(r("Artificial intelligence", "2027-01-01"), today=TODAY))

    def test_duplicates_removed(self):
        o=build([r("Marketing trends",suffix="a"),r("Marketing trends",suffix="a")],today=TODAY)
        self.assertEqual(o["total_records"],1)

    def test_reject_non_govuk(self):
        self.assertIsNone(classify({"title":"AI", "url":"https://example.net/x", "published":"2026-10-10"}, today=TODAY))

if __name__=="__main__":
    unittest.main()

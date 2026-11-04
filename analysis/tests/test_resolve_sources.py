import json
import os
import unittest

from analysis.resolve_sources import resolve, load_maps, in_app_browser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, 'analysis', 'rules', 'pro_rules.example.json'), encoding='utf-8'))
FORMS = load_maps(os.path.join(ROOT, 'maps'))   # every map file, the form map among them
UA_IG = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) Mobile/15E148 Instagram 330.0.0.40.92'


class ResolveSources(unittest.TestCase):
    def test_no_parameters_meta_form_instagram_browser(self):
        # No tracking parameters at all. The form only runs in Meta ads, and the browser is Instagram's.
        r = resolve({'form_id': 'WF-0001', 'capture_method': 'web_form', 'user_agent': UA_IG}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['pro_medium'], r['pro_category']), ('meta', 'instagram', 'Advertising'))
        self.assertEqual((r['pro_brand'], r['pro_capture_method'], r['pro_conversion_point']), ('Brand', 'Web Form', 'WF-0001'))
        self.assertEqual(r['source_basis'], 'form_default:WF-0001')
        self.assertEqual(r['medium_basis'], 'in_app:instagram')

    def test_spellings_fold_into_one_vocabulary(self):
        r = resolve({'utm_source': 'Facebook', 'utm_medium': 'Instagram', 'utm_campaign': 'lead-gen'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['pro_medium'], r['source_basis'], r['medium_basis']), ('meta', 'instagram', 'utm_source', 'utm_medium'))
        r = resolve({'utm_source': 'google', 'utm_medium': 'cpc'}, RULES, FORMS)
        self.assertEqual(r['pro_medium'], 'Search')

    def test_click_id_when_the_tags_are_missing(self):
        r = resolve({'gclid': 'Cj0K123', 'form_id': 'WF-0003'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['source_basis'], r['pro_category']), ('google', 'click_id:gclid', 'Advertising'))

    def test_unmapped_values_are_kept_and_flagged_not_guessed(self):
        r = resolve({'utm_source': 'partnerx', 'utm_medium': 'referral'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['source_basis']), ('partnerx', 'utm_source_unmapped'))
        self.assertEqual(r['pro_category'], 'zNAA')

    def test_non_web_lead_with_nothing_to_go_on_is_znaa(self):
        r = resolve({'capture_method': 'api'}, RULES, FORMS)
        self.assertEqual((r['pro_category'], r['pro_source'], r['pro_medium']), ('zNAA', 'zNAA', 'zNAA'))

    def test_web_lead_with_nothing_to_go_on_is_the_website(self):
        # No tags, click ID, form default, browser hint or referrer: the source is the website, grouped by form ID,
        # and the medium is zNAA
        r = resolve({'form_id': 'WF-0003', 'capture_method': 'web_form', 'capture_url': 'example.com/contact/'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['pro_medium']), ('website', 'zNAA'))
        self.assertEqual(r['source_basis'], 'website:WF-0003')

    def test_referrer_sets_medium_organic(self):
        r = resolve({'form_id': 'WF-0003', 'referral_url': 'https://www.facebook.com/'}, RULES, FORMS)
        self.assertEqual((r['pro_category'], r['pro_source'], r['pro_medium']), ('Organic', 'meta', 'organic'))

    def test_referrer_is_organic(self):
        r = resolve({'form_id': 'WF-0003', 'referral_url': 'https://www.google.com/search?q=funding'}, RULES, FORMS)
        self.assertEqual((r['pro_category'], r['pro_source'], r['pro_medium']), ('Organic', 'google', 'organic'))

    def test_class_says_whether_an_investment_brought_it(self):
        # Class sits above Category: Investments (ads, sponsorships, trade shows, referral partners), Inbound, zNAA
        paid = resolve({'utm_source': 'meta', 'utm_medium': 'fb', 'capture_url': 'example.com/apply/'}, RULES, FORMS)
        found = resolve({'form_id': 'WF-0003', 'referral_url': 'https://www.google.com/'}, RULES, FORMS)
        rep = resolve({'capture_method': 'manual'}, RULES, FORMS)
        unknown = resolve({}, RULES, FORMS)
        self.assertEqual((paid['pro_class'], paid['pro_category']), ('Investments', 'Advertising'))
        self.assertEqual((found['pro_class'], found['pro_category']), ('Inbound', 'Organic'))
        self.assertEqual((rep['pro_class'], rep['pro_category']), ('Inbound', 'Direct Sales'))
        self.assertEqual((unknown['pro_class'], unknown['pro_category']), ('zNAA', 'zNAA'))
        moved = resolve({'form_id': 'WF-0003', 'referral_url': 'https://www.google.com/'}, dict(RULES, category_class={'Organic': 'Investments'}), FORMS)
        self.assertEqual(moved['pro_class'], 'Investments', 'a business can move a category in the rules file')

    def test_medium_is_the_platforms_report_value(self):
        # The medium matches the value in the platform's own spend report, so leads join to spend directly
        r = resolve({'utm_source': 'google', 'utm_medium': 'pmax', 'capture_url': 'example.com/apply/'}, RULES, FORMS)
        self.assertEqual(r['pro_medium'], 'Performance Max')
        r = resolve({'utm_source': 'meta', 'utm_medium': 'fb', 'capture_url': 'example.com/apply/'}, RULES, FORMS)
        self.assertEqual(r['pro_medium'], 'facebook')

    def test_linkedin_medium_is_its_campaign_type(self):
        r = resolve({'form_id': 'WF-0003', 'utm_source': 'linkedin', 'utm_medium': 'sponsored_updates', 'utm_campaign': 'q4-demo'}, RULES, FORMS)
        self.assertEqual((r['pro_category'], r['pro_source'], r['pro_medium']), ('Advertising', 'linkedin', 'SPONSORED_UPDATES'))

    def test_own_post_is_content_not_advertising(self):
        # A post on a platform that isn't an ad is tagged <platform> / content. Nothing is ever tagged organic.
        r = resolve({'form_id': 'WF-0003', 'utm_source': 'meta', 'utm_medium': 'content'}, RULES, FORMS)
        self.assertEqual((r['pro_category'], r['pro_source'], r['pro_medium']), ('Organic', 'meta', 'content'))
        r = resolve({'form_id': 'WF-0003', 'utm_source': 'linkedin', 'utm_medium': 'content'}, RULES, FORMS)
        self.assertEqual((r['pro_category'], r['pro_source'], r['pro_medium']), ('Organic', 'linkedin', 'content'))

    def test_tests_duplicates_and_out_of_scope_are_labeled_not_deleted(self):
        r = resolve({'utm_source': 'test'}, RULES, FORMS)
        self.assertEqual(r['pro_category'], 'Test')
        r = resolve({'utm_source': 'meta', 'lead_status': 'Duplicate'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['pro_brand']), ('Duplicate', 'Duplicate'))
        self.assertEqual(resolve({'lead_status': 'out_of_scope'}, RULES, FORMS)['pro_category'], 'OoS')
        self.assertEqual(resolve({'utm_source': 'google', 'lead_status': 'spam'}, RULES, FORMS)['pro_category'], 'Spam')

    def test_capture_method_comes_from_the_record_then_the_form_map(self):
        self.assertEqual(resolve({'capture_method': 'phone_call'}, RULES, FORMS)['pro_capture_method'], 'Inbound Call')
        r = resolve({'form_id': 'LA-0001'}, RULES, FORMS)
        self.assertEqual((r['pro_capture_method'], r['capture_method_basis'], r['pro_conversion_point']), ('Third Party API', 'form_map:LA-0001', 'LA-0001'))
        self.assertEqual(resolve({'capture_method': 'import'}, RULES, FORMS)['pro_category'], 'Legacy')
        self.assertEqual(resolve({'capture_method': 'manual'}, RULES, FORMS)['pro_category'], 'Direct Sales')
        self.assertEqual(resolve({'capture_method': 'referral'}, RULES, FORMS)['pro_category'], 'Affiliate')
        r = resolve({'capture_method': 'carrier_pigeon'}, RULES, FORMS)
        self.assertEqual((r['pro_capture_method'], r['capture_method_basis']), ('carrier_pigeon', 'capture_method_unmapped'))

    def test_brand_is_the_first_cut(self):
        # hard-coded on the form first, then the capture URL's domain, then the form's row
        self.assertEqual(resolve({'brand': 'SB', 'capture_url': 'https://example.com/apply/'}, RULES, FORMS)['pro_brand'], 'Non-Brand')
        r = resolve({'capture_url': 'https://www.example-sister.com/quote/?utm_source=google'}, RULES, FORMS)
        self.assertEqual((r['pro_brand'], r['brand_basis']), ('Non-Brand', 'capture_url:domain'))
        r = resolve({'form_id': 'PH-0001', 'capture_method': 'phone_call'}, RULES, FORMS)
        self.assertEqual((r['pro_brand'], r['brand_basis']), ('Brand', 'form_map:PH-0001'))
        r = resolve({'capture_url': 'https://unknown-site.com/'}, RULES, FORMS)
        self.assertEqual((r['pro_brand'], r['brand_basis']), ('zNAA', 'brand_unmapped'))

    def test_the_97_percent_example(self):
        # 1,000 leads from Meta ads (illustrative). 30% opted out of tracking, so nothing follows them from page to
        # page. 90% filled in the Meta landing page's form (WF-0001), 10% filled in a site-wide form (WF-0003) on
        # another page. On the landing page the capture URL still carries the ad's tags, opted out or not. On another
        # page, only the visitors who allowed tracking still have them.
        TAGS = 'utm_source=meta&utm_medium=fb&utm_campaignid=120200000000101&utm_adid=120200000000901'
        leads = []
        for i in range(1000):
            opted_out = (i % 10) < 3
            on_page = i < 900
            r = {'form_id': 'WF-0001' if on_page else 'WF-0003', 'capture_method': 'web_form'}
            if on_page:
                r['capture_url'] = 'https://example.com/apply/?' + TAGS
            else:
                r['capture_url'] = 'https://example.com/contact/'
                if not opted_out:      # carried from the landing page by the capture script
                    r.update(utm_source='meta', utm_medium='fb', utm_campaignid='120200000000101')
            leads.append(resolve(r, RULES, FORMS))
        meta = sum(1 for r in leads if r['pro_source'] == 'meta')
        campaign = sum(1 for r in leads if r['campaign_key'] == 'C00001')
        self.assertEqual(meta, 970)
        self.assertEqual(campaign, 970, 'the capture URL carries the campaign for everyone who submitted on the landing page')
        self.assertEqual(sum(1 for r in leads if r['source_basis'] == 'capture_url:utm_source'), 900)

    def test_without_the_capture_url_tags_the_form_id_still_carries_the_source(self):
        # Tags stripped before the page loaded (an app or a redirect): the form ID still says meta, the campaign is gone.
        r = resolve({'form_id': 'WF-0001', 'capture_method': 'web_form', 'capture_url': 'https://example.com/apply/'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['source_basis'], r['pro_campaign']), ('meta', 'form_default:WF-0001', 'zNAA'))

    def test_tags_are_read_from_the_capture_url(self):
        url = 'https://example.com/get-started/?utm_source=google&utm_medium=cpc&utm_campaignid=21000000002&gclid=Cj0K'
        r = resolve({'capture_url': url, 'capture_method': 'web_form'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['pro_medium'], r['pro_campaign'], r['pro_category']), ('google', 'Search', 'Search · funding', 'Advertising'))
        self.assertEqual((r['source_basis'], r['medium_basis'], r['campaign_basis']), ('capture_url:utm_source', 'capture_url:utm_medium', 'capture_url:campaign_map:utm_campaignid'))
        r = resolve({'capture_url': 'https://example.com/contact/?fbclid=IwAR1'}, RULES, FORMS)
        self.assertEqual((r['pro_source'], r['source_basis']), ('meta', 'capture_url:click_id:fbclid'))

    def test_capture_group_web_and_non_web_from_the_capture_url(self):
        r = resolve({'capture_url': 'https://example.com/apply/', 'form_id': 'WF-0001'}, RULES, FORMS)
        self.assertEqual((r['pro_capture_group'], r['capture_group_basis']), ('Web', 'capture_url'))
        r = resolve({'capture_method': 'phone_call'}, RULES, FORMS)
        self.assertEqual((r['pro_capture_group'], r['capture_group_basis']), ('Non-Web', 'no_capture_url'))
        # an ad platform's lead form arrives through its integration: online, but not the website
        self.assertEqual(resolve({'form_id': 'LA-0001'}, RULES, FORMS)['pro_capture_group'], 'Non-Web')
        # a web form whose URL went missing is still Web, with a basis that flags the gap at the form
        r = resolve({'capture_method': 'web_form'}, RULES, FORMS)
        self.assertEqual((r['pro_capture_group'], r['capture_group_basis']), ('Web', 'capture_method_no_url'))

    def test_campaign_resolves_by_id_through_the_map(self):
        # the campaign was renamed after the click: the id still finds it, and reports carry one key
        r = resolve({'utm_source': 'meta', 'utm_campaignid': '120200000000101', 'utm_campaign': 'old-name'}, RULES, FORMS)
        self.assertEqual((r['pro_campaign'], r['campaign_key'], r['campaign_basis']), ('Lead gen · revenue', 'C00001', 'campaign_map:utm_campaignid'))
        r = resolve({'utm_source': 'google', 'utm_campaign': 'search-brand'}, RULES, FORMS)
        self.assertEqual((r['campaign_key'], r['campaign_basis']), ('C00003', 'campaign_map:utm_campaign'))
        r = resolve({'utm_source': 'meta', 'utm_campaignid': '999'}, RULES, FORMS)
        self.assertEqual((r['pro_campaign'], r['campaign_key'], r['campaign_basis']), ('999', '', 'utm_campaignid_unmapped'))

    def test_the_raw_row_is_never_changed(self):
        row = {'utm_source': 'Facebook', 'utm_medium': 'Instagram', 'capture_method': 'web_form'}
        before = dict(row)
        resolve(row, RULES, FORMS)
        self.assertEqual(row, before)

    def test_in_app_detection(self):
        self.assertEqual(in_app_browser(UA_IG), 'instagram')
        self.assertEqual(in_app_browser('Mozilla/5.0 [FBAN/FBIOS;FBAV/470.0]'), 'facebook')
        self.assertEqual(in_app_browser('Mozilla/5.0 Safari/604.1'), '')


if __name__ == '__main__':
    unittest.main()

import unittest
from sanskrit_beginners_content import LESSONS

class BeginnerContentTests(unittest.TestCase):
    def test_curriculum(self):
        self.assertEqual(len(LESSONS),18)
        self.assertEqual(len({x['id'] for x in LESSONS}),18)
        self.assertTrue(all(len(x['questions'])==3 for x in LESSONS))
    def test_answers(self):
        for lesson in LESSONS:
            for q in lesson['questions']:
                self.assertTrue(0<=q['answer']<len(q['options']))
    def test_stages(self):
        self.assertTrue(all(x['stage']=='Script' for x in LESSONS[:6]))
        self.assertTrue(all(x['stage']!='Script' for x in LESSONS[6:]))
if __name__=='__main__':unittest.main()

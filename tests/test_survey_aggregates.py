import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from aggregate_survey import aggregate
class SurveyAggregateTests(unittest.TestCase):
 def row(self,i,status='pending',review='accepted'):
  return {'id':str(i),'review_status':review,'payload':{'region':'PL-MZ','permit':'temporary','status':status,'elapsed_days':i+1,'applied_date':'2025-01-01','nationality':'BY','email':'private@example.invalid'}}
 def test_only_reviewed_rows_and_minimum_group_size(self):
  self.assertEqual(aggregate([self.row(i) for i in range(9)])['cells'],[])
  r=aggregate([self.row(i) for i in range(10)]+[self.row(99,review='unreviewed')]);self.assertEqual(r['cells'][0]['n'],10);self.assertEqual(r['cells'][0]['median_days'],5.5)
 def test_pending_and_concluded_are_separate(self):
  r=aggregate([self.row(i) for i in range(10)]+[self.row(i+10,status='positive') for i in range(10)])
  self.assertEqual({c['measure'] for c in r['cells']},{'pending_elapsed_age','concluded_duration'})
 def test_duplicate_ids_and_personal_fields_excluded(self):
  rows=[self.row(i) for i in range(10)];r=aggregate(rows+[rows[0]])
  self.assertEqual(r['cells'][0]['n'],10);self.assertNotIn('email',str(r));self.assertNotIn('2025-01-01',str(r));self.assertNotIn('nationality',str(r))
 def test_threshold_cannot_be_lowered(self):
  with self.assertRaises(ValueError):aggregate([],min_n=2)
if __name__=='__main__':unittest.main()

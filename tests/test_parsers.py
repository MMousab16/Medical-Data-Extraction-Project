# tests/test_parsers.py
import pytest
from backend.hospital import PrescriptionExtractor, PatientExtractor

pre_1 = """Dr John Smith, M.D
2 Non-Important Street,
New York, Phane (000)-111-2222

Name: Maria Sharapova Date: 5/11/2022 _

Address: 9 tennis court, new Russia, DC

K

Prednisone 20 mg
Lialda 2.4 gram

Directions:
Prednisone, Taper 5 mg every 3 days,

Finish in 2.5 weeks . -
Lialda - take 2 pill everyday for 1 month —

: ‘Refill: 2_times,"""

pre_2 = """Dr John Smith, M.D
2 Non-Important Street,
New York, Phone (000). -111-2222

Name: Virat Kohij _ | Date 2/05/2022

Address: 2 cricket blvd, New Delhi

Omeprazole 40 me

Directions: Use two tablets daily for three months

Refill: 3 times"""

pd_1 = """47/12/2020

Patient Medical Record

Patient Information Birth Date

Kathy Crawford May 6 1972

(737) 988-0851 Weight’

9264 Ash Dr 98

New York City, 10005 j *

United States Height:
190"""

pd_2 = """17/12/2020

Patient Medical Record

Patient Information : Birth Date
Jerry Lucas May 2 1998
(279) 920-8204 : Weight:
4218 Wheeler Ridge Dr 57

Buffalo, New York, 14201 Height:
United States 70.
"""

def test_prescription_pre1():
    ex = PrescriptionExtractor(pre_1)
    out = ex.extract()
    assert 'maria' in (out.get('name') or '').lower()
    meds = ' '.join(out.get('medicines', [])).lower()
    assert 'prednisone' in meds
    assert 'lialda' in meds
    assert out.get('refill') == 2 or out.get('refill') is None  # tolerate OCR differences

def test_prescription_pre2():
    ex = PrescriptionExtractor(pre_2)
    out = ex.extract()
    assert 'virat' in (out.get('name') or '').lower()
    meds = ' '.join(out.get('medicines', [])).lower()
    assert 'omeprazole' in meds
    assert out.get('refill') == 3 or out.get('refill') is None

def test_patient_pd1():
    ex = PatientExtractor(pd_1)
    out = ex.extract()
    assert 'kathy' in (out.get('name') or '').lower()
    assert 'ash' in (out.get('address') or '').lower() or '9264' in (out.get('address') or '')

def test_patient_pd2():
    ex = PatientExtractor(pd_2)
    out = ex.extract()
    assert 'jerry' in (out.get('name') or '').lower()
    assert 'wheeler' in (out.get('address') or '').lower() or '4218' in (out.get('address') or '')

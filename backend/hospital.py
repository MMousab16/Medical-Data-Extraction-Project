# backend/hospital.py
import re
from typing import List, Dict

class Hospital:
    def __init__(self, text: str):
        self.text = text or ""
        # normalize whitespace
        self.normalized = re.sub(r'\r', '', self.text)

    def _lines(self) -> List[str]:
        return [ln.strip() for ln in self.normalized.splitlines()]

    def extract(self) -> Dict:
        raise NotImplementedError("Subclasses implement extract()")


class PrescriptionExtractor(Hospital):
    """
    Extract: name, date, address, medicines (list), directions (string), refill (int or None)
    """
    def extract(self) -> Dict:
        lines = [ln for ln in self._lines() if ln.strip() != ""]
        text = self.normalized

        # ---- Name ----
        name = None
        for ln in lines:
            if ln.lower().startswith('name'):
                # take right of colon, split by Date if OCR squashed them
                part = ln.split(':', 1)[1] if ':' in ln else ln
                part = part.split('Date')[0]
                part = re.sub(r'[_\|\:]+', ' ', part).strip()
                name = re.sub(r'[^A-Za-z \-\.]', '', part).strip()
                break

        # fallback: regex search
        if not name:
            m = re.search(r'Name[:\s]*([A-Z][A-Za-z\-\.\' ]{2,})', text)
            if m:
                name = m.group(1).strip()

        # ---- Date ----
        date = None
        m = re.search(r'Date[:\s]*([0-3]?\d[\/\-][0-1]?\d[\/\-]\d{2,4})', text, re.IGNORECASE)
        if m:
            date = m.group(1).strip()
        else:
            # try other date formats e.g. 17/12/2020 at top of patient files
            m2 = re.search(r'\b([0-3]?\d[\/\-][0-1]?\d[\/\-]\d{2,4})\b', text)
            if m2:
                date = m2.group(1).strip()

        # ---- Address ----
        address = None
        addr_index = None
        for idx, ln in enumerate(lines):
            if ln.lower().startswith('address'):
                addr_index = idx
                # get content after colon and maybe next lines until Directions or blank
                raw = ln.split(':', 1)[1] if ':' in ln else ''
                addr_parts = [raw.strip()] if raw.strip() else []
                for j in range(idx+1, min(len(lines), idx+4)):
                    nxt = lines[j]
                    if nxt.lower().startswith('directions') or nxt.lower().startswith('name') or re.match(r'^[A-Za-z]{1}$', nxt):
                        break
                    addr_parts.append(nxt)
                address = ' '.join([p for p in addr_parts if p]).strip()
                break

        # fallback: first line that looks like street (contains digits and street words)
        if not address:
            for ln in lines:
                if re.search(r'\d', ln) and not re.search(r'\(\d{3}\)', ln) and len(ln) > 5:
                    if any(word in ln.lower() for word in ['dr', 'street', 'st', 'rd', 'blvd', 'ave', 'court', 'ash']):
                        address = ln.strip()
                        break

        # ---- Medicines ----
        medicines: List[str] = []
        # find index of 'Directions'
        dir_idx = None
        for idx, ln in enumerate(lines):
            if ln.lower().startswith('directions'):
                dir_idx = idx
                break

        meds_start = addr_index + 1 if addr_index is not None else 0
        meds_end = dir_idx if dir_idx is not None else len(lines)
        for ln in lines[meds_start:meds_end]:
            # skip lines that are obviously headers
            if ln.lower().startswith(('name', 'date', 'address')):
                continue
            # ignore stray 1-letter lines
            if len(ln.strip()) <= 2:
                continue
            # treat this as medicine line
            medicines.append(ln.strip())

        # ---- Directions ----
        directions = None
        if dir_idx is not None:
            dir_parts = []
            for j in range(dir_idx, len(lines)):
                if lines[j].lower().startswith('refill'):
                    break
                if j == dir_idx:
                    # remove the 'Directions:' label
                    part = lines[j].split(':', 1)
                    part = part[1] if len(part) > 1 else ''
                    dir_parts.append(part.strip())
                else:
                    dir_parts.append(lines[j].strip())
            directions = ' '.join([p for p in dir_parts if p]).strip()

        # ---- Refill ----
        refill = None
        mref = re.search(r'Refill[:\s]*([0-9]+)', text, re.IGNORECASE)
        if mref:
            try:
                refill = int(mref.group(1))
            except:
                refill = None

        return {
            "type": "prescription",
            "name": name,
            "date": date,
            "address": address,
            "medicines": medicines,
            "directions": directions,
            "refill": refill
        }


class PatientExtractor(Hospital):
    """
    Extract minimal patient info: name and address (based on heuristics).
    """
    MONTHS = r'(Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)'

    def extract(self) -> Dict:
        lines = [ln for ln in self._lines() if ln.strip() != ""]
        text = self.normalized

        name = None
        address = None

        # 1) Try to find a line that contains a person's name followed by a month (common in your sample)
        m = re.search(r'([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+){1,2})\s+' + self.MONTHS + r'\s+\d{1,2}\s+\d{2,4}', text)
        if m:
            name = m.group(1).strip()

        # 2) fallback: pick first line near 'Patient' heading that looks like a name
        if not name:
            for i, ln in enumerate(lines):
                if re.search(r'patient information', ln, re.IGNORECASE):
                    # check next 3 lines for a likely name (two capitalized words)
                    for j in range(i+1, min(i+5, len(lines))):
                        cand = lines[j]
                        # candidate contains at least two alphabetic words with capital first letter
                        if re.match(r'^[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)+', cand):
                            # take first two words as name
                            name = ' '.join(cand.split()[:2])
                            break
                if name:
                    break

        # 3) as last resort: find any line with two Titlecase words
        if not name:
            for ln in lines:
                parts = ln.split()
                if len(parts) >= 2 and parts[0][0].isupper() and parts[1][0].isupper() and not re.search(r'\d', ln):
                    # avoid picking "United States" as name
                    if 'United' in ln or 'States' in ln:
                        continue
                    name = parts[0] + ' ' + parts[1]
                    break

        # ---- Address: look for a line that contains digits and street keywords, exclude phone numbers
        for i, ln in enumerate(lines):
            if re.search(r'\(\d{3}\)\s*\d{3}', ln):  # phone skip
                continue
            if re.search(r'\d', ln) and not re.search(r'phone|weight|height|birth|in case of emergency', ln, re.IGNORECASE):
                if any(word in ln.lower() for word in ['dr', 'street', 'st', 'rd', 'blvd', 'ave', 'court', 'drive', 'dr', 'ridge', 'ash', 'blvd', 'wheeler']):
                    address = ln.strip()
                    # append next line if it looks like city/state/zip
                    if i+1 < len(lines) and re.search(r'\d{5}', lines[i+1]):
                        address = address + ", " + lines[i+1].strip()
                    break

        # Final result
        return {
            "type": "patient",
            "name": name,
            "address": address
        }

from typing import List, Dict
import csv

csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)

def _strip(data: List[str]) -> List[str]:
    return [s.strip() for s in data]

def _filter(data: Dict[str,str]) -> Dict[str,str]:
    return {key: value for (key, value) in data.items() if key != '' and value != ''}

class Parser:
    @staticmethod
    def csv_to_json(input: str) -> List[Dict[str,str]]:
        data = []
        reader = csv.reader(input, dialect='piper')
        header = _strip(next(reader))
        for row in reader:
            data.append(_filter(dict(zip(header, _strip(row)))))
        return data

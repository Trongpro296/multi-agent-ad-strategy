"""Shared advertising CSV schema and pre-write structural validation."""
import csv
import io
import json
import math


CSV_COLUMNS = {
    'sources.csv': ('id','claim','source_url','access_date','scope','evidence_type'),
    'media_plan.csv': ('channel','role','objective','segment_id','offer_id','budget_pct','budget_amount','currency','start','end','landing_page','assumption'),
    'budget_scenarios.csv': ('scenario','channel','budget_amount','metric','metric_value','formula','assumption'),
    'creative_matrix.csv': ('concept_id','segment_id','insight','hook','benefit','proof','cta','format','asset_requirement','test_variant'),
    'experiment_plan.csv': ('test_id','hypothesis','variant_a','variant_b','primary_metric','min_sample','duration_days','decision_rule',
                            'test_type','sample_unit','sample_basis','data_source','business_kpi','decision_supported',
                            'decision_not_supported','decision_owner','prerequisites','missing_data_rule','start','end'),
    'execution_calendar.csv': ('week','start','end','channel','activity','owner','deliverable'),
}


class CSVWriteValidationError(ValueError):
    def __init__(self, path, detail):
        self.path = path
        super().__init__(f'CSV rejected before writing {path}: {detail}. File unchanged. '
                         'Correct the CSV and call save_file again; do not report it saved.')


def validate_ad_csv(path, data):
    """Validate complete candidate bytes, including an append, without changing them."""
    name = path.rsplit('/', 1)[-1]
    required = CSV_COLUMNS[name]
    reader = None
    try:
        reader = csv.reader(io.StringIO(data.decode('utf-8-sig'), newline=''), strict=True)
        header = next(reader, [])
        if len(set(header)) != len(header) or not set(required).issubset(header):
            raise CSVWriteValidationError(path, f'header must contain {list(required)!r}; received {header!r}')
        count = 0
        for row in reader:
            if not row:  # Match DictReader's handling of physical blank lines.
                continue
            count += 1
            if len(row) != len(header):
                raise CSVWriteValidationError(path, f'record {count}, ending line {reader.line_num}: '
                    f'expected {len(header)} cells, received {len(row)}; quote commas/newlines inside cells. '
                    f'Header={header!r}; parsed cells={[str(cell)[:90] for cell in row[:20]]!r}. '
                    'Safer: pass content as a JSON string with columns (header names) and rows (objects keyed by those names); save_file serializes and quotes CSV automatically. Do not remove Vietnamese accents to fix delimiters')
        if not count:
            raise CSVWriteValidationError(path, 'at least one data row is required, not a header alone')
        if name == 'sources.csv':
            from utils.ad_delivery_policy import source_issues_csv
            findings=source_issues_csv(data)
            if findings:raise CSVWriteValidationError(path,'; '.join(f['code']+': '+f['message'] for f in findings))
    except (UnicodeError, csv.Error) as exc:
        line = reader.line_num if reader is not None else 1
        raise CSVWriteValidationError(path, f'invalid UTF-8/CSV near line {line}: {exc}') from exc


def serialize_csv_table(path,content,*,existing_header=None,include_header=True):
    """Serialize named cells without guessing how to repair ambiguous raw CSV."""
    try:
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('duplicate JSON key: '+key)
                result[key]=value
            return result
        table=json.loads(content.lstrip('\ufeff \t\r\n'),object_pairs_hook=unique)
        if not isinstance(table,dict) or set(table)!={'columns','rows'}:
            raise ValueError('CSV JSON requires exactly columns and rows')
        columns=table['columns'];rows=table['rows']
        if not isinstance(columns,list) or not columns or any(not isinstance(c,str) or not c.strip() for c in columns):raise ValueError('columns must be a list of nonempty names')
        if len(set(columns))!=len(columns) or not set(CSV_COLUMNS[path.rsplit('/',1)[-1]]).issubset(columns):raise ValueError('columns must be unique and include required schema names')
        if existing_header is not None and columns!=existing_header:raise ValueError('append columns/order must match the existing CSV header')
        if not isinstance(rows,list) or not 1<=len(rows)<=5000:raise ValueError('rows must contain 1..5000 objects')
        normalized=[]
        for index,row in enumerate(rows,1):
            if not isinstance(row,dict):raise ValueError('row '+str(index)+' must be an object')
            if set(row)!=set(columns):raise ValueError('row '+str(index)+' keys must exactly match columns; missing='+str(sorted(set(columns)-set(row)))+'; extra='+str(sorted(set(row)-set(columns))))
            values={}
            for key,value in row.items():
                if value is None:values[key]=''
                elif isinstance(value,bool) or not isinstance(value,(str,int,float)) or (isinstance(value,float) and not math.isfinite(value)):
                    raise ValueError('row '+str(index)+', column '+key+': expected text, finite number or null')
                else:values[key]=value
            normalized.append(values)
        output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=columns,quoting=csv.QUOTE_ALL,lineterminator='\r\n')
        if include_header:writer.writeheader()
        writer.writerows(normalized)
        return output.getvalue()
    except (ValueError,TypeError,KeyError) as exc:
        raise CSVWriteValidationError(path,'invalid structured CSV table: '+str(exc)) from exc

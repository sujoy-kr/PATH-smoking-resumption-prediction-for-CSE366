"""Build or verify/reuse the immutable local stage 4 cohort; report aggregates only."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.cohort import CohortError, build_cohort
from path_project.feature_validation import validate_feature_mapping

if __name__=='__main__':
    try:
        errors=validate_feature_mapping(ROOT)
        if errors:
            raise CohortError(f'Feature mapping preflight failed with {len(errors)} errors; run scripts/validate_feature_mapping.py --no-write.')
        result=build_cohort(ROOT)
    except CohortError as error:
        print(f'Cohort build stopped: {error}',file=sys.stderr)
        raise SystemExit(1)
    summary=result['summary']
    print(f"Mode: {result['mode']}; labeled={summary['labeled_records']}; unique_people={summary['unique_labeled_people']}; positive={summary['positive_outcomes']}; unobserved={summary['unobserved_interval_outcomes']}")

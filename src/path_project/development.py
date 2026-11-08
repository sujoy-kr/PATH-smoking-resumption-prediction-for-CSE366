"""Tuning-only descriptive exploration and final-input metadata; no fitting."""
import csv
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
from path_project.cohort import json_write, harmonize_features, validate_ids
from path_project.evaluation import load_locked, BoundaryError, participant_weights
from path_project.documentation import fingerprint


def ensure_tuning(frame, people, config):
    allowed=set(people.loc[people['participant_role'].eq('tuning'),'PERSONID'])
    if not set(frame['PERSONID']).issubset(allowed) or frame['starting_wave'].gt(config['development_max_start_wave']).any() or frame['followup_wave'].gt(7).any():
        raise BoundaryError('Exploration contains a non-tuning participant or future interval; no values emitted.')


def load_tuning(root, settings):
    config,cc,lock,people,rows=load_locked(root)
    allowed=people.loc[people['participant_role'].eq('tuning'),'PERSONID'].tolist()
    filters=[('PERSONID','in',allowed),('starting_wave','<=',config['development_max_start_wave'])]
    mapping=json.loads((root/cc['feature_mapping']).read_text())
    selected=['PERSONID','starting_wave','followup_wave','outcome_p30d']
    for name in mapping['candidate_predictor_names']:
        selected.extend([name,name+'__reason'])
    cohort=pd.read_parquet(root/cc['output_dir']/cc['files']['cohort'],columns=selected,filters=filters)
    ledger=pd.read_parquet(root/cc['output_dir']/cc['files']['ledger'],filters=filters)
    ensure_tuning(cohort,people,config);ensure_tuning(ledger,people,config)
    expected=rows.loc[rows['partition'].eq('tuning'),['PERSONID','starting_wave','followup_wave']]
    if set(map(tuple,expected.to_numpy()))!=set(map(tuple,cohort[expected.columns].to_numpy())):
        raise BoundaryError('Tuning exploration keys differ from the locked tuning partition.')
    # The ledger contains labels from stage 4; discard them immediately. Attrition
    # needs observation status only, never outcomes for an unobserved interview.
    ledger=ledger[['PERSONID','starting_wave','followup_wave','observation_status']]
    return config,cc,lock,people,mapping,cohort,ledger


def attrition_baselines(root, settings, cc, mapping, ledger):
    project=json.loads((root/cc['project_config']).read_text())
    originals=json.loads((root/cc['input_manifest']).read_text())
    fields=[f for f in mapping['fields'] if f['name'] in settings['attrition_features']]
    partial={**mapping,'fields':fields}
    pieces=[];audit=[]
    for wave in sorted(ledger['starting_wave'].unique()):
        wave=int(wave)
        if wave>6:raise BoundaryError('No future-wave raw data permitted in exploration.')
        meta=ledger.loc[ledger['starting_wave'].eq(wave)]
        ids=set(meta['PERSONID'])
        source=next(w['data'] for w in project['waves'] if w['wave']==wave)
        if fingerprint(root/source)!=originals[source]['sha256']:raise BoundaryError('Original baseline input changed.')
        columns=sorted({'PERSONID'}|{col for f in fields for col in f['waves'][str(wave)]['source_columns']})
        matched=[]
        # TSV cannot push down participant predicates. Only earlier-wave selected
        # columns are read in chunks; immediately discard all non-tuning-ledger rows.
        for chunk in pd.read_csv(root/source,sep='\t',usecols=columns,dtype='string',keep_default_na=False,na_filter=False,encoding=cc['read_encoding'],chunksize=settings['raw_chunk_rows']):
            keep=chunk.loc[chunk['PERSONID'].isin(ids)]
            if not keep.empty:matched.append(keep)
        raw=pd.concat(matched,ignore_index=True)
        validate_ids(raw,wave,'PERSONID',cc['invalid_identifiers'])
        if set(raw['PERSONID'])!=ids:raise BoundaryError('Missing tuning baseline answers in canonical source.')
        features,_=harmonize_features(raw,wave,partial,cc)
        joined=pd.concat([raw[['PERSONID']].reset_index(drop=True),features],axis=1)
        pieces.append(meta.merge(joined,on='PERSONID',how='left',validate='one_to_one'))
        audit.append({'starting_wave':wave,'source':source,'source_sha256':originals[source]['sha256'],'columns_read':columns,'rows_harmonized':len(raw),'filter':'Only tuning participants eligible in this baseline ledger; no other responses summarized.'})
    return pd.concat(pieces,ignore_index=True),audit


def recency_groups(series, settings):
    result=pd.cut(series.astype(float),bins=settings['recency_bin_edges_days'],labels=settings['recency_bin_labels'],right=True,include_lowest=True).astype('string')
    result=result.mask(series.gt(settings['recency_bin_edges_days'][-1]).fillna(False),'over 100 years (review)')
    return result.fillna('Unknown / skipped')


def aggregate(cohort, ledger, baseline, mapping, settings):
    interval=[];missing=[];numeric=[];distributions=[];attrition=[]
    fields={f['name']:f for f in mapping['fields']}
    for wave,data in cohort.groupby('starting_wave'):
        weights=participant_weights(data)
        interval.append({'starting_wave':int(wave),'pair':f'{wave}-{wave+1}','records':len(data),'people':int(data['PERSONID'].nunique()),'positive':int(data['outcome_p30d'].sum()),'prevalence':float(data['outcome_p30d'].mean()),'participant_weighted_prevalence':float(np.average(data['outcome_p30d'].astype(float),weights=weights))})
        for name in mapping['candidate_predictor_names']:
            observed=int(data[name].notna().sum())
            missing.append({'starting_wave':int(wave),'feature':name,'records':len(data),'observed':observed,'missing_fraction':1-observed/len(data),'reasons':{str(k):int(v) for k,v in data[name+'__reason'].value_counts().items()}})
    for name in mapping['candidate_predictor_names']:
        values=cohort[name].dropna().astype(float)
        f=fields[name]
        if f['output_labels']:
            if not set(values).issubset({float(code) for code in f['output_labels']}):raise BoundaryError('Harmonized category outside documented labels.')
            for code,label in f['output_labels'].items():distributions.append({'feature':name,'label':label,'count':int(cohort[name].eq(float(code)).sum())})
            distributions.append({'feature':name,'label':'Unknown / skipped','count':int(cohort[name].isna().sum())})
        else:
            threshold=settings['review_flags'].get(name)
            numeric.append({'feature':name,'units':f['output_units'],'observed':len(values),'missing':int(cohort[name].isna().sum()),'minimum':float(values.min()) if len(values) else None,'p25':float(values.quantile(.25)) if len(values) else None,'median':float(values.median()) if len(values) else None,'p75':float(values.quantile(.75)) if len(values) else None,'p99':float(values.quantile(.99)) if len(values) else None,'maximum':float(values.max()) if len(values) else None,'review_threshold':threshold,'above_review_threshold':int(values.gt(threshold).sum()) if threshold else 0,'negative_observed_values':int(values.lt(0).sum())})
    recency=recency_groups(cohort['last_cigarette_recency_days'],settings).value_counts()
    contributions=cohort.groupby('PERSONID').size()
    repeats={str(k):int(v) for k,v in contributions.value_counts().sort_index().items()}
    for wave in [None,*sorted(baseline['starting_wave'].unique())]:
        data=baseline if wave is None else baseline.loc[baseline['starting_wave'].eq(wave)]
        for name in settings['attrition_features']:
            labels=recency_groups(data[name],settings) if name=='last_cigarette_recency_days' else data[name].map(lambda v:fields[name]['output_labels'].get(str(int(v)),'Unknown / skipped') if pd.notna(v) else 'Unknown / skipped')
            for label in sorted(labels.unique()):
                block=data.loc[labels.eq(label)]
                observed=int(block['observation_status'].eq('observed_valid').sum())
                attrition.append({'starting_wave':'pooled' if wave is None else int(wave),'feature':name,'category':label,'eligible_intervals':len(block),'people':int(block['PERSONID'].nunique()),'observed_outcomes':observed,'missing_interviews':int(block['observation_status'].eq('missing_followup_interview').sum()),'unknown_present_outcomes':int(block['observation_status'].eq('invalid_followup_outcome').sum()),'observed_fraction':observed/len(block)})
    summary={'scope':'Tuning participants only; starting Waves 1–6; no calibration/threshold/test exploration','labeled_records':len(cohort),'labeled_people':int(cohort['PERSONID'].nunique()),'positives':int(cohort['outcome_p30d'].sum()),'eligible_intervals':len(ledger),'eligible_people':int(ledger['PERSONID'].nunique()),'unobserved_outcomes':int(ledger['observation_status'].ne('observed_valid').sum()),'people_with_repeated_records':int(contributions.gt(1).sum()),'repeated_records_beyond_first':len(cohort)-len(contributions),'repeat_distribution':repeats,'recency_distribution':{str(k):int(v) for k,v in recency.items()},'no_model_fitting':True,'final_test_features_or_outcomes_read':False}
    return {'summary':summary,'interval_prevalence':interval,'missingness':missing,'numeric_distributions':numeric,'categorical_distributions':distributions,'followup_by_baseline':attrition}


def figures(root, output, tables, settings):
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'figure.dpi':140})
    def save(fig,name):
        fig.savefig(output/(name+'.png'),bbox_inches='tight');plt.close(fig)
    data=pd.DataFrame(tables['interval_prevalence'])
    fig,ax=plt.subplots(figsize=(8,4));ax.bar(data['pair'],100*data['prevalence']);ax.set(xlabel='Adjacent survey interval',ylabel='Positive outcomes (%)',title='Next-survey smoking: tuning records only');save(fig,'interval_prevalence')
    data=pd.DataFrame(tables['missingness']).pivot(index='feature',columns='starting_wave',values='missing_fraction')
    fig,ax=plt.subplots(figsize=(10,10));im=ax.imshow(data.to_numpy(),vmin=0,vmax=1,aspect='auto',cmap='YlOrRd');ax.set_yticks(range(len(data)),data.index);ax.set_xticks(range(len(data.columns)),[f'{w}→{w+1}' for w in data.columns]);ax.set_title('Missing candidate responses by interval (tuning labeled rows)');fig.colorbar(im,ax=ax,label='Fraction missing');save(fig,'missingness')
    order=settings['recency_bin_labels']+['over 100 years (review)','Unknown / skipped'];values=tables['summary']['recency_distribution']
    fig,ax=plt.subplots(figsize=(9,5));ax.barh(order,[values.get(k,0) for k in order]);ax.set(xlabel='Tuning labeled interval records',title='Observed raw quit/last-cigarette recency and missingness');save(fig,'quit_recency')
    fig,axes=plt.subplots(2,3,figsize=(13,8));names=['age_band','education_level','employment_status','physical_health','mental_health','home_combustible_smoking_rules']
    for ax,name in zip(axes.flat,names):
        data=[r for r in tables['categorical_distributions'] if r['feature']==name];ax.barh([r['label'] for r in data],[r['count'] for r in data]);ax.set_title(name.replace('_',' '));ax.tick_params(axis='y',labelsize=8)
    fig.suptitle('Baseline responses: tuning labeled intervals');fig.tight_layout();save(fig,'feature_distributions')
    counts=tables['summary']['repeat_distribution'];fig,ax=plt.subplots(figsize=(7,4));ax.bar(list(counts),list(counts.values()));ax.set(xlabel='Labeled intervals per person',ylabel='Tuning people',title='Repeated observations stay within participant folds');save(fig,'repeated_observations')
    data=[r for r in tables['followup_by_baseline'] if r['starting_wave']=='pooled' and r['feature']=='age_band'];fig,ax=plt.subplots(figsize=(8,4));ax.barh([f"{r['category']} (n={r['eligible_intervals']:,})" for r in data],[100*r['observed_fraction'] for r in data]);ax.set(xlim=(0,100),xlabel='Valid observed next outcome (%)',title='Follow-up availability by baseline age (tuning eligible intervals)');save(fig,'followup_availability')


def run_exploration(root):
    root=Path(root);settings=json.loads((root/'configs/development_exploration.json').read_text())
    config,cc,lock,people,mapping,cohort,ledger=load_tuning(root,settings)
    baseline,audit=attrition_baselines(root,settings,cc,mapping,ledger)
    ensure_tuning(baseline,people,config)
    tables=aggregate(cohort,ledger,baseline,mapping,settings)
    output=root/settings['output_dir'];output.mkdir(parents=True,exist_ok=True)
    for name,value in tables.items():json_write(output/(name+'.json'),value)
    json_write(output/'access_audit.json',{'scope':tables['summary']['scope'],'parquet_predicates':'PERSONID in locked tuning people; starting_wave <=6','canonical_baselines':audit,'test_features_or_outcomes_read':False,'calibration_threshold_used':False,'raw_tsv_limitation':'No participant predicate pushdown in TSV; chunk-filter earlier-wave raw selected columns before any harmonization or summary.'})
    figures(root,output,tables,settings)
    return tables,settings,mapping

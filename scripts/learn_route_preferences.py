"""Constrained pooled route-choice baseline using public Singapore observations.
A simplified model informed by Melnikov et al. (2022), not a reproduction of
its hierarchical model. Learns distance/sun preferences; no traffic labels.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/route_preference_model'
DATA=ROOT/'data/processed/75023_75024_75025_75074_buffer250m/singapore_sun_present_choices.csv'


def fit_choice(x,y,sun=True):
    matrix=-x[:,:2 if sun else 1]
    def objective(beta):
        logits=matrix@beta
        loss=np.mean(np.logaddexp(0,logits)-y*logits)
        grad=matrix.T@(expit(logits)-y)/len(y)
        return loss,grad
    result=minimize(objective,np.full(matrix.shape[1],.02),jac=True,method='L-BFGS-B',
                    bounds=[(1e-8,None)]+([(0,None)] if sun else []),options={'maxiter':2000,'ftol':1e-12,'gtol':1e-8})
    if not result.success:raise RuntimeError('Route preference optimization failed: '+result.message)
    return result.x


def scores(y,p):
    p=np.clip(p,1e-12,1-1e-12)
    return {'log_loss':float(np.mean(-y*np.log(p)-(1-y)*np.log1p(-p))),
            'brier_score':float(np.mean((p-y)**2)),
            'accuracy':float(np.mean((p>=.5)==y)),'observations':len(y)}


def equivalent_distance(length_m,sun_exposed_m,penalty):
    length=np.asarray(length_m,dtype=float);sun=np.asarray(sun_exposed_m,dtype=float)
    if penalty<0 or not np.isfinite(penalty) or np.any(length<0) or np.any(sun<0) or np.any(sun>length):
        raise ValueError('Need nonnegative lengths, 0 <= sun <= length and finite nonnegative penalty.')
    return length+penalty*sun


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=pd.read_csv(DATA);people=np.array(sorted(data.participant.unique()))
    heldout=set(np.random.default_rng(42).permutation(people)[:max(1,int(np.ceil(.2*len(people))))])
    test=data.participant.isin(heldout).to_numpy();train=~test
    x=data[['delta_length_b_minus_a','delta_sun_length_b_minus_a']].to_numpy();y=data.b_chosen.to_numpy()
    beta=fit_choice(x[train],y[train]);base=fit_choice(x[train],y[train],sun=False)
    p=expit(-x[test]@beta);pbase=expit(-x[test,0]*base[0])
    majority=float(y[train].mean())
    evaluation={'distance_only':scores(y[test],pbase),'distance_and_sun':scores(y[test],p),
                'constant_training_choice_rate':scores(y[test],np.full(test.sum(),majority))}
    # Grouped cross-validation addresses the instability of one small holdout.
    folds=np.array_split(np.random.default_rng(42).permutation(people),5)
    oof_sun=np.zeros(len(data));oof_base=np.zeros(len(data));fold_results=[]
    for fold_id,fold_people in enumerate(folds):
        mask=data.participant.isin(fold_people).to_numpy()
        b=fit_choice(x[~mask],y[~mask]);d=fit_choice(x[~mask],y[~mask],sun=False)
        oof_sun[mask]=expit(-x[mask]@b);oof_base[mask]=expit(-x[mask,0]*d[0])
        fold_results.append({'fold':fold_id,'test_participants':len(fold_people),
            'distance_only':scores(y[mask],oof_base[mask]),'distance_and_sun':scores(y[mask],oof_sun[mask])})
    cross_validation={'folds':5,'split_unit':'participant','distance_only':scores(y,oof_base),
        'distance_and_sun':scores(y,oof_sun),'by_fold':fold_results}

    # Refit for optional application only after preserving the independent evaluation.
    full=fit_choice(x,y);penalty=float(full[1]/full[0])
    payload={'model':'Pooled binary route-choice logit; no intercept; monotone distance and sun costs',
        'source_paper':'https://doi.org/10.1038/s41598-022-06383-5','source_data':'https://osf.io/aj4vk/',
        'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
        'observations':len(data),'participants':len(people),'training_participants':int(data.loc[train,'participant'].nunique()),
        'test_participants':len(heldout),'split':'Participant-grouped 80/20, seed=42; no shared participants',
        'test_metrics':evaluation,'grouped_cross_validation':cross_validation,'evaluation_beta_distance':float(beta[0]),'evaluation_beta_sun':float(beta[1]),
        'full_data_beta_distance':float(full[0]),'full_data_beta_sun':float(full[1]),
        'full_data_extra_sun_distance_factor':penalty,
        'edge_cost_form':'equivalent_meters = length_m + extra_sun_distance_factor * sun_exposed_m',
        'scope':'Both labels and features are from Singapore experimental routes. No traffic/crossing/temperature coefficients learned.',
        'limitations':['Simplified pooled model, not the published hierarchical model.',
            'Small single-city experiment; grouped cross-validation is not external validation or a confidence interval.',
            'Not validated for Plano or specific mobility profiles.',
            'Tree cover is not observed sun exposure. Any canopy-to-sun substitution is an additional scenario assumption.',
            'No traffic/sidewalk/crossing labels in training; these trade-offs remain unsupported.',
            'Not automatically applied to the Plano graph or map.'],
        'geoai_description':'An empirically fitted geospatial route-preference baseline; no imagery inference or deep learning performed.'}
    (OUT/'model_and_evaluation.json').write_text(json.dumps(payload,indent=2))
    predictions=data.loc[test,['participant','trial','b_chosen']].copy();predictions['p_b_distance_only']=pbase;predictions['p_b_distance_sun']=p
    predictions.to_csv(OUT/'heldout_predictions.csv',index=False)
    oof=data[['participant','trial','b_chosen']].copy();oof['p_b_distance_only']=oof_base;oof['p_b_distance_sun']=oof_sun
    oof.to_csv(OUT/'grouped_oof_predictions.csv',index=False)
    pd.DataFrame({'participant':people,'split':['test' if p in heldout else 'train' for p in people]}).to_csv(OUT/'participant_split.csv',index=False)
    print(json.dumps(payload,indent=2),flush=True)

if __name__=='__main__':main()

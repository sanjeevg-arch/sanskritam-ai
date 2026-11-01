"""Administrator-only usage metrics, based on Supabase request logs."""
from collections import defaultdict
from datetime import date, timedelta, timezone, datetime
import pandas as pd
import streamlit as st
from corrections import is_admin
from private_beta import _request, BetaError, setting

# USD per 1 million tokens; editable in Streamlit Secrets when rates change.
# Defaults are illustrative estimates, NOT verified live pricing.
def rate(name, default):
    try: return max(0.0, float(setting(name) or default))
    except (ValueError, TypeError): return default

def estimate(row):
    if row.get('state') != 'completed': return None
    if row.get('model') != 'gpt-4.1-mini': return None
    a,b = int(row.get('input_tokens') or 0), int(row.get('output_tokens') or 0)
    if not a and not b: return None
    return (a * rate('COST_GPT41_MINI_INPUT_PER_M', 0.40) + b * rate('COST_GPT41_MINI_OUTPUT_PER_M', 1.60))/1_000_000

def fetch_usage(days=30):
    # A date-only PostgREST filter avoids URL-encoded timezone punctuation issues.
    cutoff=(datetime.now(timezone.utc)-timedelta(days=days)).date().isoformat()
    # Pagination avoids silently truncating at Supabase's usual 1,000-row default.
    rows=[]
    for start in range(0, 20000, 1000):
        path=('/rest/v1/beta_requests?select=created_at,usage_day,email,state,total_tokens,'
              'input_tokens,output_tokens,operation,model&usage_day=gte.'+cutoff
              +'&order=created_at.desc&limit=1000&offset='+str(start))
        batch=_request('GET',path,service=True)
        if not isinstance(batch,list): raise BetaError('Unexpected usage response.')
        rows.extend(batch)
        if len(batch)<1000: return rows,False
    return rows,True

def render_admin_cost_dashboard(user):
    if not is_admin(user): return
    with st.expander('💰 AI Cost & Admin Dashboard · Admin only',expanded=False):
        st.caption('Private usage data. Estimates are not OpenAI invoices. Costs for audio transcription and legacy rows may be unknown.')
        days=st.selectbox('Reporting window (UTC)',[7,30,90],index=1,key='admin_cost_days')
        if st.button('Refresh AI usage',key='admin_cost_refresh',use_container_width=True): st.rerun()
        try: rows,truncated=fetch_usage(days)
        except BetaError as exc:
            st.error('Usage unavailable: '+str(exc))
            st.info('In Supabase SQL Editor, run admin_cost_diagnostics.sql included in this package. Confirm all expected beta_requests columns exist. If a column is missing, rerun admin_cost_setup.sql.'); return
        if truncated: st.warning('Showing the newest 20,000 records only; totals may be incomplete.')
        if not rows: st.info('No AI requests in the selected reporting window.'); return
        done=[r for r in rows if r.get('state')=='completed']
        failed=[r for r in rows if r.get('state')=='failed']
        costs=[estimate(r) for r in done]
        known=[x for x in costs if x is not None]
        a,b,c,d=st.columns(4)
        a.metric('Requests',len(rows)); b.metric('Completed',len(done)); c.metric('Failed',len(failed)); d.metric('Known cost estimate',f'${sum(known):.4f}')
        st.caption(f'{len(done)-len(known)} completed requests have unpriced or unavailable token usage; known-cost total is a lower-bound estimate, not full spend.')
        a,b,c=st.columns(3)
        a.metric('Recorded tokens',f'{sum(int(r.get("total_tokens") or 0) for r in done):,}')
        b.metric('Unique users',len(set(r.get('email','') for r in rows)))
        c.metric('Reserved / in progress',len(rows)-len(done)-len(failed))
        daily=defaultdict(lambda:{'Requests':0,'Completed':0,'Estimated USD':0.0})
        for r in rows:
            day=str(r.get('usage_day') or str(r.get('created_at',''))[:10]); daily[day]['Requests']+=1
            if r.get('state')=='completed': daily[day]['Completed']+=1
            daily[day]['Estimated USD']+=estimate(r) or 0
        chart=pd.DataFrame([{'Day':day,**v} for day,v in sorted(daily.items())]).set_index('Day')
        st.markdown('**Daily request volume**'); st.bar_chart(chart[['Requests','Completed']])
        st.markdown('**Estimated daily cost (USD, priced requests only)**'); st.line_chart(chart[['Estimated USD']])
        by_op=defaultdict(lambda:{'Requests':0,'Tokens':0,'Estimated USD':0.0})
        for r in rows:
            op=str(r.get('operation') or 'unknown'); by_op[op]['Requests']+=1
            by_op[op]['Tokens']+=int(r.get('total_tokens') or 0)
            by_op[op]['Estimated USD']+=estimate(r) or 0
        st.markdown('**Usage by operation**')
        st.dataframe(pd.DataFrame([{'Operation':k,**v} for k,v in sorted(by_op.items())]),hide_index=True,use_container_width=True)
        st.markdown('**Top users by request count**')
        by_user=defaultdict(lambda:{'Requests':0,'Completed':0,'Estimated USD':0.0})
        for r in rows:
            k=str(r.get('email') or 'unknown'); by_user[k]['Requests']+=1
            by_user[k]['Completed']+=r.get('state')=='completed'
            by_user[k]['Estimated USD']+=estimate(r) or 0
        st.dataframe(pd.DataFrame([{'User':k,**v} for k,v in sorted(by_user.items(),key=lambda x:-x[1]['Requests'])[:50]]),hide_index=True,use_container_width=True)
        st.download_button('Download usage summary CSV',chart.to_csv().encode('utf-8'),file_name='sanskritam_usage_summary.csv',mime='text/csv',key='admin_cost_csv')
        st.caption('Pricing defaults: gpt-4.1-mini input $0.40/M, output $1.60/M. Change via COST_GPT41_MINI_INPUT_PER_M and COST_GPT41_MINI_OUTPUT_PER_M. Verify rates with OpenAI before relying on estimates. Audio/image billing can differ; image estimates use reported tokens but may omit special billing details.')

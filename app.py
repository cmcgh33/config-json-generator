"""Launch with: python -m streamlit run app.py"""
from pathlib import Path

import streamlit as st

from src.app_service import compile_workbook, WorkbookError

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / 'examples/sample_input.xlsx'

st.set_page_config(page_title='Config JSON Generator | Carla McGhee', page_icon='{}', layout='wide')
st.markdown('''<style>
.block-container {max-width:1200px;padding-top:2.6rem;padding-bottom:2rem;}
h1 {letter-spacing:-.04em;}
.hero-label {color:#6558d3;font-weight:700;font-size:.78rem;letter-spacing:.14em;}
.hero-copy {font-size:1.12rem;color:#5d6678;max-width:760px;margin-bottom:1.8rem;}
[data-testid="stMetric"] {background:#f4f3fb;border-radius:12px;padding:16px;}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero-label">CARLA MCGHEE / PORTFOLIO PROJECT 01</div>', unsafe_allow_html=True)
st.title('Business rules. Clean JSON.')
st.markdown('<div class="hero-copy">Turn a configuration workbook into validated JSON. Check the rules, review the result, and download a consistent file.</div>', unsafe_allow_html=True)


def clear_result():
    st.session_state.pop('result', None)
    st.session_state.pop('processing_error', None)


def process(content, source_label):
    clear_result()
    try:
        result = compile_workbook(content)
        result['source_label'] = source_label
        st.session_state['result'] = result
    except WorkbookError as exc:
        st.session_state['processing_error'] = str(exc)


left, right = st.columns([.38, .62], gap='large')
with left:
    with st.container(border=True):
        st.subheader('1. Choose your workbook')
        st.caption('Start with the template. Edit its amber cells in Excel, then upload your saved copy.')
        st.download_button('Download Excel template', data=TEMPLATE.read_bytes(),
                           file_name='config_input_template.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           key='template_download', width='stretch')
        upload = st.file_uploader('Upload configuration workbook', type=['xlsx'], key='workbook_upload',
                                  on_change=clear_result, help='Model, Factors, and Rules tabs. Up to 5 MB.')
        if st.button('Validate and generate', type='primary', key='generate',
                     disabled=upload is None, width='stretch'):
            with st.spinner('Checking your configuration…'):
                process(upload.getvalue(), upload.name)
        st.divider()
        st.markdown('**Just exploring?**')
        st.caption('Try the fictional four-factor example without uploading a file.')
        if st.button('Try fictional example', key='example', width='stretch'):
            process(TEMPLATE.read_bytes(), 'Fictional example workbook')
    with st.expander('Workbook essentials'):
        st.markdown('''- **Model:** model ID and display name.
- **Factors:** labels, types, units, and weights.
- **Rules:** numeric bands or category values and scores.

Weights must total **100%**. Keep numeric bands in order, with no gaps or overlaps. Enter 40 for 40%.''')

with right:
    st.subheader('2. Review and download')
    error = st.session_state.get('processing_error')
    result = st.session_state.get('result')
    if error:
        st.error('The workbook needs a correction before a JSON file can be generated.')
        st.text(error)
        st.caption('Correct the indicated input in Excel, save, and upload the revised workbook.')
    elif result:
        config = result['config']
        st.success('Input checks, output schema, and business rules passed.')
        st.caption(f'Source: {result["source_label"]}')
        a, b, c = st.columns(3)
        a.metric('Factors', len(config['factors']))
        b.metric('Scoring rules', sum(len(f['rules']) for f in config['factors']))
        c.metric('Total weight', f'{sum(f["weight"] for f in config["factors"]):.0%}')
        overview, rules, json_tab = st.tabs(['Overview', 'Rules', 'JSON preview'])
        with overview:
            st.markdown(f'**{config["model"]["name"]}**')
            st.dataframe([{'Factor':f['label'], 'Type':f['type'], 'Unit':f['unit'],
                           'Weight (%)':round(f['weight']*100, 8)} for f in config['factors']],
                         hide_index=True, width='stretch')
        with rules:
            st.caption('Numeric minimums are included; maximums are excluded. Higher scores mean higher risk.')
            for factor in config['factors']:
                with st.expander(factor['label']):
                    if factor['type'] == 'numeric':
                        rows = [{'Minimum':str(r['min']) if r['min'] is not None else 'Unbounded',
                                 'Maximum':str(r['max']) if r['max'] is not None else 'Unbounded',
                                 'Score':r['score']} for r in factor['rules']]
                    else:
                        rows = [{'Value':r['value'], 'Score':r['score']} for r in factor['rules']]
                    st.dataframe(rows, hide_index=True, width='stretch')
        with json_tab:
            st.code(result['payload'], language='json', line_numbers=True)
        st.download_button('Download validated JSON', data=result['payload'],
                           file_name=result['filename'], mime='application/json',
                           key='json_download', type='primary', width='stretch')
    else:
        with st.container(border=True):
            st.markdown('### Your configuration will appear here')
            st.write('Upload a workbook or try the fictional example to see the factors, scoring rules, and generated JSON.')
            st.caption('A download becomes available after all validation checks pass.')

st.divider()
st.caption('Independent portfolio project by Carla McGhee. Sample values are fictional. Configuration generation does not evaluate borrowers or make lending decisions.')

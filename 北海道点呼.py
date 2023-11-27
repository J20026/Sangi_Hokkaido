import streamlit as st
import psycopg2
import pandas as pd
import datetime
from PIL import Image

#im=Image.open("./ito.png")
#st.set_page_config(page_icon=im)

#更新時間で色付ける？
#登録したらformをクリア
def click_add_button():
    st.session_state.companion.append(0)
def click_del_button():
    if len(st.session_state.companion)!=0:
        del st.session_state.companion[-1]

def check_situation(val):
    b='green' if val=='帰宿' else 'red' if val=='外出' else 'yellow' if val=='その他' else ''
    c='black' if val=='その他' else ''
    return 'background-color: '+b+'; color:'+c

conn = psycopg2.connect(
    user="agr",
    password="agr",
    host="133.125.39.70",
    port="5432",
    dbname="TEN"
)
if "member" not in st.session_state:
    st.session_state.member = pd.read_sql("select * from tsuchi.member order by 氏名", con=conn)
    st.session_state.companion=[]

st.title("北海道点呼")

with st.form("form"):
    name = st.selectbox(label='名前', options=['']+list(st.session_state.member['氏名']))
    for i in range(len(st.session_state.companion)):
        st.session_state.companion[i]=st.selectbox(label='名前'+str(i+2), options=['']+list(st.session_state.member['氏名']))
    add_button,del_button=st.columns(2)
    with add_button:
        add_button=st.form_submit_button("同行者追加",on_click=click_add_button)
    with del_button:
        del_button=st.form_submit_button("同行者削除",on_click=click_del_button)
    situation = st.selectbox(label='現在の状態', options=['','外出','帰宿','その他'])
    memo = st.text_area('memo(行く場所、予定時間など)')
    submitted = st.form_submit_button("送信")

if submitted:
    if all(i!='' for i in st.session_state.companion) and name!='' and situation!='':
        cur=conn.cursor()
        cur.execute("insert into tsuchi.status values('%s','%s','%s')" % (name,situation,memo))
        for i in range(len(st.session_state.companion)):
            cur.execute("insert into tsuchi.status values('%s','%s','%s')" % (st.session_state.companion[i],situation,memo))
        conn.commit()
        cur.close()
        st.success('登録しました')
    else:
        st.error('入力されていない項目があります(memoを除く)')
st.button('更新')
status=pd.read_sql("select distinct on(氏名) 氏名,状態,memo,TO_CHAR(更新時刻 + INTERVAL '9 HOURS', 'YYYY/MM/DD HH24:MI:SS') from(select * from tsuchi.status where (氏名,更新時刻) in (select 氏名,max(更新時刻) from tsuchi.status group by 氏名) order by case 状態 when '外出' then 1 when 'その他' then 2 when '帰宿' then 3 end,氏名) a", con=conn)
status=status.style.applymap(check_situation,subset=['状態'])
st.table(status)

url='https://sistkanri-my.sharepoint.com/:w:/g/personal/umehara_takahito_sist_ac_jp/EX62-2AEGlRLmkYiOlk4LCMBhwKkLNwvp-PFCKJnJ0c4xQ?e=OXLSdN'
st.write('[しおり](%s)' % url)

conn.close()

#https://qiita.com/nockn/items/15e081b58e02a0878855
#https://data-analytics.fun/2022/07/11/streamlit-state-callback/#toc2
#https://chayarokurokuro.hatenablog.com/entry/2021/02/25/175922#51-%E6%9D%A1%E4%BB%B6%E3%81%AB%E3%81%AF%E3%81%BE%E3%82%8B%E6%96%87%E5%AD%97%E3%81%AE%E8%89%B2%E3%82%92%E5%A4%89%E3%81%88%E3%82%8B%E9%96%A2%E6%95%B0%E3%82%92%E4%BD%9C%E3%82%8B

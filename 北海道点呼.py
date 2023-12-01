import streamlit as st
import psycopg2
import pandas as pd
import datetime
from PIL import Image
import hashlib

#データベースへの接続
conn = psycopg2.connect(
    user=st.secrets.DBConnection.user,
    password=st.secrets.DBConnection.password,
    host=st.secrets.DBConnection.host,
    port=st.secrets.DBConnection.port,
    dbname=st.secrets.DBConnection.dbname
)
cur = conn.cursor()
st.set_page_config(initial_sidebar_state="expanded")

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

# ユーザ認証
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False
    
def login_user(username, password):
    cur.execute('SELECT * FROM hokkaido.usertable WHERE username = %s AND password = %s',(username, password))
    data = cur.fetchall()
    conn.commit()
    return data

def login_input():
    st.sidebar.text("ログインしたらしおりと名前が見えるよ")
    username = st.sidebar.text_input("ユーザー名を入力してください", key="loguser", placeholder="例) user", disabled=st.session_state.initial_load)
    password = st.sidebar.text_input("パスワードを入力してください", key="logpass", type='password', disabled=st.session_state.initial_load, placeholder="例) password")
    onbutton = st.sidebar.button("ログイン", disabled=False, key="button")
    if onbutton or st.session_state['a']:
        if(len(username) != 0 and len(password) != 0):
            hashed_pswd = make_hashes(password)
            result = login_user(username, check_hashes(password, hashed_pswd))
            if result:
                st.session_state['a']= True
                st.sidebar.success("{}さんでログインしました".format(username))
                st.session_state.initial_load=True
                st.session_state['error']=False
                # ログイン成功後の画面を表示
            else:
                st.sidebar.error("ユーザー名かパスワードが間違っています")
        else:
            st.sidebar.warning("ユーザ名とパスワードを1文字以上で入力して下さい")


def main():
    if 'initial_load' not in st.session_state:
        st.session_state.initial_load = False
    login_input()

    if "member" not in st.session_state:
        st.session_state.member = pd.read_sql("select left(氏名,6) as 氏名 from hokkaido.member order by 氏名;", con=conn)
        st.session_state.companion=[]
    if(st.session_state['a']):
        st.title("北海道点呼(ログイン中)")
    else:
        st.title("北海道点呼(未ログイン)")

    with st.form("form"):
        if(st.session_state['a']):
            st.session_state.member = pd.read_sql("select * from hokkaido.member order by 氏名", con=conn)
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
            if(st.session_state['a']):
                cur.execute("insert into hokkaido.status values('%s','%s','%s')" % (name,situation,memo))
            else:
                name1="'"+name+"%'"
                cur.execute("insert into hokkaido.status values((select * from hokkaido.member where \"氏名\" like %s),'%s','%s')" % (name1,situation,memo))
            for i in range(len(st.session_state.companion)):    
                if(st.session_state['a']):
                    cur.execute("insert into hokkaido.status values('%s','%s','%s')" % (st.session_state.companion[i],situation,memo))
                else:
                    name1="'"+st.session_state.companion[i]+"%'"
                    cur.execute("insert into hokkaido.status values((select * from hokkaido.member where \"氏名\" like %s),'%s','%s')" % (name1,situation,memo))
            conn.commit()
            cur.close()
            st.success('登録しました')
        else:
            st.error('入力されていない項目があります(memoを除く)')
    if(st.button('更新')):
        st.snow()
        st.baloon()
    if(st.session_state['a']):
        status=pd.read_sql("select distinct on(氏名) 氏名,状態,memo,TO_CHAR(更新時刻 + INTERVAL '9 HOURS', 'YYYY/MM/DD HH24:MI:SS') as 更新時刻 from(select * from hokkaido.status where (氏名,更新時刻) in (select 氏名,max(更新時刻) from hokkaido.status group by 氏名) order by case 状態 when '外出' then 1 when 'その他' then 2 when '帰宿' then 3 end,氏名) a;", con=conn)
    else:
        status=pd.read_sql("select distinct on(氏名) left(氏名,6) as 氏名,状態,memo,TO_CHAR(更新時刻 + INTERVAL '9 HOURS', 'YYYY/MM/DD HH24:MI:SS') as 更新時刻 from(select * from hokkaido.status where (氏名,更新時刻) in (select 氏名,max(更新時刻) from hokkaido.status group by 氏名) order by case 状態 when '外出' then 1 when 'その他' then 2 when '帰宿' then 3 end,氏名) a;", con=conn)
    status=status.style.applymap(check_situation,subset=['状態'])
    st.table(status)

    url=st.secrets.url.bookmark
    if(st.session_state['a']):
        st.write('[しおり](%s)' % url)

if __name__ == '__main__':
    if 'a' not in st.session_state:
        st.session_state['a'] = False
    main()

#データベース接続をクローズ
cur.close()    
conn.close()

#https://qiita.com/nockn/items/15e081b58e02a0878855
#https://data-analytics.fun/2022/07/11/streamlit-state-callback/#toc2
#https://chayarokurokuro.hatenablog.com/entry/2021/02/25/175922#51-%E6%9D%A1%E4%BB%B6%E3%81%AB%E3%81%AF%E3%81%BE%E3%82%8B%E6%96%87%E5%AD%97%E3%81%AE%E8%89%B2%E3%82%92%E5%A4%89%E3%81%88%E3%82%8B%E9%96%A2%E6%95%B0%E3%82%92%E4%BD%9C%E3%82%8B

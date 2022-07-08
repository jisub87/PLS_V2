import streamlit as st
import pandas as pd
import common_utils
import os
pd.set_option('display.float_format','{:,}'.format)

@st.cache
def load_store():
    return common_utils.read_data(os.path.join('data','store.p')).sort_values('매장명', ascending=True)

@st.cache
def load_data():
    store_res = pd.read_csv('predict_data20220628_20220705.csv')
    store_res['SALE_DT'] = store_res['SALE_DT'].astype(str)
    store_res['STOR_CD'] = store_res['STOR_CD'].astype(str)
    return store_res

# 예측 결과이용, 결과 테이블 생성
def get_pls_prediction_data(store_res, SALE_DT, STOR_CD):
    STOR_CD = int(STOR_CD)
    y_list = ['와퍼패티', '버거패티', '스테이크패티', '언양식불고기패티', '도넛치킨패티', 'BK새우패티', '롱치킨패티', '킹치킨패티',
              '뉴올리언스치킨패티', 'BK치즈패티', '플랜트패티', 'BK뉴치킨패티', '통다리치킨패티']
    store_res['SALE_DT'] = store_res['SALE_DT'].astype(str)
    store_res['STOR_CD'] = store_res['STOR_CD'].astype(int)
    criteria = (store_res['SALE_DT'] == SALE_DT)&(store_res['STOR_CD']==STOR_CD)
    one_store_res = store_res[criteria].reset_index(drop=True)
    if len(one_store_res)>=1:
        sale_data = one_store_res[['ORD_TIME','SALE_AMT']]

        sale_data = pd.concat([sale_data,sale_data.iloc[1:,1].reset_index(drop=True)], axis=1).fillna(0)
        sale_data.columns = ['ORD_TIME','SALE_AMT','temp_sale']
        sale_data['PEAK_1HR'] = sale_data.iloc[:,1]+sale_data.iloc[:,2]
        D3 = sale_data['PEAK_1HR'].max()
        BASE = BLE = D3/6
        '{}천원'.format(int(round(BLE/1000,0)))
        sale_data['1HR'] = sale_data.iloc[:,1] * 2
        M54 = max(D3, sale_data['1HR'].max())
        H3 = M54/BLE
        TOTAL_SALES = sale_data['SALE_AMT'].sum()

        res = {'출력 날짜':'', 'DATA 날짜':SALE_DT, '매출':int(TOTAL_SALES), '매장명':STOR_CD, 'BLE':int(round(BLE,0)), 'PEAK 레벨':round(H3,1)}

        sale_data['STOCK_LEVELS'] = sale_data['1HR']/BLE
        intervals = [0,1.49,2.49,3.49,4.49,5.49,6.49,999]
        sale_data['PRODUCT'] = pd.cut(sale_data['STOCK_LEVELS'], bins= intervals, labels=["L 1","L 2","L 3","L 4","L 5","L 6","PEAK"]).astype(str)
        sale_data['PRODUCT'] = sale_data['PRODUCT'].apply(lambda x: "Lv 0" if x.find('nan')>=0 else x)
        sale_data['CUM_SALE_AMT'] = sale_data['SALE_AMT'].cumsum()
        sale_data['user_records'] = ""
        df1 = sale_data[['ORD_TIME','SALE_AMT','PRODUCT','CUM_SALE_AMT','user_records']]

        selection_columns = ['ORD_TIME']+y_list
        df2 = one_store_res[selection_columns]

        df = pd.merge(df1, df2, on='ORD_TIME', how='left')
        df['ORD_TIME'] = df['ORD_TIME'].apply(lambda x: f'{x:08d}')
        df['TIME_Frame'] = df['ORD_TIME'].apply(lambda x: str(x)[0:2]+":"+str(x)[2:4])

        res2 = df[['ORD_TIME','TIME_Frame','SALE_AMT','PRODUCT','CUM_SALE_AMT','user_records']+y_list]
        for col in ['SALE_AMT','CUM_SALE_AMT']+y_list:
            res2[col] = res2[col].astype(int)
        return res, res2
    else:
        print('데이터 없음')
        return {}, {}
def get_pls_prediction_test_data(res2, SALE_DT, STOR_CD):
    STOR_CD = int(STOR_CD)
    test = common_utils.read_data(os.path.join('data', 'check_data.p'))
    test['SALE_DT'] = test['SALE_DT'].astype(str).str.strip()
    test['STOR_CD'] = test['STOR_CD'].astype(int)
    check_test = test[(test['STOR_CD'] == STOR_CD) & (test['SALE_DT'] == SALE_DT)]
    print(check_test.columns)
    print(res2.columns)
    check_columns = [x for x in check_test.columns if x in res2.columns]
    y_list = [x for x in check_columns if
              x in ['와퍼패티', '버거패티', '스테이크패티', '언양식불고기패티', '도넛치킨패티', 'BK새우패티', '롱치킨패티', '킹치킨패티',
                    '뉴올리언스치킨패티', 'BK치즈패티', '플랜트패티', 'BK뉴치킨패티', '통다리치킨패티']]
    check_pred = pd.merge(res2, check_test[check_columns], on='ORD_TIME', how='left', suffixes=['', '_pred'])
    pred_diff_data = pd.DataFrame()
    pred_diff_data['PRODUCT'] = check_pred['PRODUCT']
    pred_diff_data['ORD_TIME'] = check_pred['ORD_TIME']
    pred_diff_data['SALE_DT'] = SALE_DT
    pred_diff_data['STOR_CD'] = STOR_CD
    for col in ['SALE_AMT'] + y_list:
        pred_diff_data[col] = check_pred[col + '_pred'] - check_pred[col]
    res3 = pred_diff_data
    res4 = res3.describe()
    return res3, res4


if __name__ == '__main__':
    st.title("PLS")
    st.header("패티 수요 예측")

    #data_load_state = st.text('준비중...')
    store = load_store()
    #data_load_state.text("완료")

    # 매장명 리스트
    store_names = store['매장명'].to_list()

    # 매장명 선택
    option = st.sidebar.selectbox('매장선택', store_names)

    #날짜 선택
    date = st.sidebar.date_input('날짜')
    st.sidebar.write('선택 매장:', option)
    st.sidebar.write('선택 날짜:', date)

    store_code = store.loc[store['매장명']==option,'코드'].reset_index(drop=True)[0]
    # date = '2022-06-28'
    # store_code = 9
    SALE_DT = str(date).replace('-','')
    STOR_CD = str(store_code)
    print('input:',SALE_DT,STOR_CD)

    store_res = pd.read_csv('data/predict_data20220628_20220705.csv')
    res1, res2 = get_pls_prediction_data(store_res, SALE_DT, STOR_CD)
    st.subheader("Information")
    st.write('주요 정보를 노출')
    st.dataframe(pd.DataFrame(res1, index=[0]))

    st.subheader("Predction Results")
    st.write('시간별 패티수량, 매출, 피크타임 등 예측정보를 노출')
    st.dataframe(res2)

    if len(res2)>=1:
        res3, res4 = get_pls_prediction_test_data(res2, SALE_DT, STOR_CD)
        st.subheader("Difference Comparison: Predction - Actual")
        st.write('예측된 패티수와 실제 사용된 패티수의 차이를 비교')
        st.dataframe(res3)

        st.subheader("Statistics of Difference Comparison")
        st.write('차이에 대한 통계적 정보')
        st.dataframe(res4)
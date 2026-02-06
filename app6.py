import streamlit as st
import pandas as pd
import plotly.express as px  # 인터랙티브 그래프 라이브러리 추가
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# 한글 폰트 설정
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="인사평가 소수점 정밀 분석", layout="wide")
st.title("📈 2025 인사평가 정밀 데이터 분석 시스템")

uploaded_file = st.file_uploader("소수점 점수가 포함된 엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # 1. 소수점 데이터 형식 강제 변환 (float64)
    # 50.1 ~ 99.9 범위를 정확히 인식하기 위함
    target_cols = ['성과점수', '역량점수', '총점', '근무기간', '전년도총점']
    for col in target_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(float).fillna(0.0)

    # 상단 대시보드 (소수점 첫째자리까지 표시)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 인원", f"{len(df)}명")
    c2.metric("평균 총점", f"{df['총점'].mean():.2f}점")
    if '전년도총점' in df.columns:
        growth_avg = (df['총점'] - df['전년도총점']).mean()
        c3.metric("평균 성장폭", f"{growth_avg:+.2f}점")
    c4.metric("평균 근속", f"{df['근무기간'].mean():.1f}년")

    st.divider()

    # --- 순서 정의 (사용자 요청 반영) ---
    rank_order = ['부장', '차장', '과장', '대리', '사원']
    grade_order = ['S', 'A', 'B', 'C', 'D']

    # Pandas 데이터프레임에 정렬 순서 적용 (Categorical 타입 변환)
    if '직급' in df.columns:
        df['직급'] = pd.Categorical(df['직급'], categories=rank_order, ordered=True)
    if '종합등급' in df.columns:
        df['종합등급'] = pd.Categorical(df['종합등급'], categories=grade_order, ordered=True)

    # 탭 구성
    # 탭 구성에 tab8 추가
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "[부서/직급]", "[9-Box Matrix]", "[근속 성과]", "[등급 분포]",
        "[핵심인재]", "[성과 성장 분석]", "[리스크 & 코칭]", "[조직 성장 엔진]"
    ])

    with tab1:
        st.subheader("직급별 평균 성과 (부장 → 사원 순)")

        # 직급별 평균 계산 (정렬된 직급 순서 유지)
        if '직급' in df.columns:
            rank_avg = df.groupby('직급', observed=True)['총점'].mean().reset_index()

            # Plotly 막대 그래프로 시각화
            fig_rank = px.bar(
                rank_avg,
                x='직급',
                y='총점',
                color='직급',
                category_orders={'직급': rank_order},  # x축 순서 고정
                text_auto='.1f',
                title="직급별 평균 총점 비교",
                template='plotly_white'
            )
            st.plotly_chart(fig_rank, width='stretch')

            # 부서별 점수 분포 (Box Plot)
            st.subheader("부서별 성과 점수 분포")
            fig_dept = px.box(
                df, x='부서', y='총점', color='부서',
                points="all",  # 모든 데이터 점 표시
                hover_data=['성명', '직급', '사번'],
                template='plotly_white'
            )
            st.plotly_chart(fig_dept, width='stretch')

    with tab2:
        st.subheader("성과-역량 9-Box Matrix")
        st.caption("점이 클수록 총점이 높습니다. 마우스를 올리면 상세 정보가 표시됩니다.")

        # category_orders를 사용하여 등급 순서 고정
        fig1 = px.scatter(
            df, x='역량점수', y='성과점수',
            color='종합등급', size='총점',
            hover_name='성명',
            hover_data=['사번', '부서', '총점', '근무기간'],
            category_orders={'종합등급': grade_order},  # <--- 이 부분이 순서를 결정합니다
            color_discrete_map={'S': '#FFD700', 'A': '#1f77b4', 'B': '#2ca02c', 'C': '#ff7f0e', 'D': '#d62728'},
            # 등급별 색상 고정 (선택사항)
            labels={'역량점수': '역량 (잠재력)', '성과점수': '성과 (현재)'},
            template='plotly_white'
        )

        fig1.add_vline(x=df['역량점수'].mean(), line_dash="dash", line_color="red")
        fig1.add_hline(y=df['성과점수'].mean(), line_dash="dash", line_color="red")

        st.plotly_chart(fig1, width='stretch')

    with tab3:
        st.subheader("전년 대비 성과 변화 추적")
        if '전년도총점' in df.columns:
            # 변화량 계산
            df['변화량'] = df['총점'] - df['전년도총점']

            fig2 = px.scatter(
                df,
                x='전년도총점',
                y='총점',
                color='변화량',
                color_continuous_scale='RdBu_r',  # 상승은 파랑, 하락은 빨강 계열
                hover_name='성명',
                hover_data=['사번', '부서', '변화량'],
                labels={'전년도총점': '2024년 점수', '총점': '2025년 점수'}
            )

            # 기준선(y=x) 추가
            max_val = max(df['총점'].max(), df['전년도총점'].max())
            fig2.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                           line=dict(color="Gray", dash="dash"))

            st.plotly_chart(fig2, width='stretch')
            st.info("점선보다 위에 있는 점이 전년 대비 성적이 오른 직원입니다.")

    with tab4:
        with tab4:
            st.subheader("종합등급 분포")
            if '종합등급' in df.columns:
                grade_counts = df['종합등급'].value_counts().sort_index()
                st.bar_chart(grade_counts)
            st.dataframe(df)

    with tab5:
        st.subheader("핵심인재 프로파일링")
        star_threshold = df['총점'].quantile(0.9)
        stars = df[df['총점'] >= star_threshold]
        st.write(f"**상위 10% 기준점:** {star_threshold:.2f}점")
        st.dataframe(stars.sort_values(by='총점', ascending=False))

    with tab6:
        st.subheader("전년 대비 성과 성장자(Top Improvers) 추적")

        # 1. 전년도 데이터가 있는지 확인
        if '전년도총점' in df.columns:
            # 변화량 및 변화율 계산
            df['점수변화량'] = df['총점'] - df['전년도총점']
            # 핵심: size에 사용할 절대값 컬럼을 별도로 생성
            df['변화량_절대값'] = df['점수변화량'].abs()
            df['성장률(%)'] = (df['점수변화량'] / df['전년도총점'] * 100).replace([np.inf, -np.inf], 0)

            col_up, col_down = st.columns(2)

            with col_up:
                st.write("**최고 성장자 TOP 5 (상승폭 기준)**")
                top_improvers = df.sort_values(by='점수변화량', ascending=False).head(5)
                st.table(top_improvers[['성명', '부서', '전년도총점', '총점', '점수변화량']])

            with col_down:
                st.write("**부서별 평균 성장폭**")
                dept_growth = df.groupby('부서')['점수변화량'].mean().sort_values()
                st.bar_chart(dept_growth)

            # 시각화: 전년 vs 올해 점수 산점도
            st.write("**전년도 점수 vs 올해 점수 비교**")

            fig6 = px.scatter(
                df, x='전년도총점', y='총점',
                color='부서', size='변화량_절대값',
                hover_name='성명',
                labels={'전년도총점': '2024년 총점 (전년)', '총점': '2025년 총점 (당해)'},
                template='plotly_white'
            )

            # --- 빨간색 점선(y=x 기준선) 추가 시작 ---
            # 차트의 범위를 결정하기 위해 최대/최소값 계산
            max_val = max(df['총점'].max(), df['전년도총점'].max())
            min_val = min(df['총점'].min(), df['전년도총점'].min())

            fig6.add_shape(
                type="line",
                x0=min_val, y0=min_val, x1=max_val, y1=max_val,
                line=dict(color="Red", width=2, dash="dash"),
                layer="below"  # 점이 선 위에 오도록 설정
            )
            # --- 빨간색 점선 추가 끝 ---

            st.plotly_chart(fig6, width='stretch')

            st.info("빨간 점선 위에 위치한 인원이 전년 대비 성적이 향상된 직원들입니다.")
        else:
            st.warning("데이터에 '전년도총점' 컬럼이 없습니다. 분석을 위해 전년도 데이터를 포함해 주세요.")

    with tab7:
        st.subheader("성과 리스크 및 코칭 대상자 분석")
        st.caption("역량과 성과의 불균형이 있거나 성적이 급락한 인원을 집중 관리합니다.")

        # 1. 잠재력 미발휘군 (High Potential, Low Performance)
        # 역량은 평균 이상인데 성과는 평균 이하인 인원
        potential_risk = df[(df['역량점수'] > df['역량점수'].mean()) & (df['성과점수'] < df['성과점수'].mean())]

        # 2. 성적 급락자 (Shock Drop) - 전년도 데이터가 있을 경우
        if '전년도총점' in df.columns:
            df['점수차이'] = df['총점'] - df['전년도총점']
            warning_drop = df[df['점수차이'] <= -10].sort_values(by='점수차이')  # 10점 이상 하락

        col_risk1, col_risk2 = st.columns(2)

        with col_risk1:
            st.error(f"잠재력 미발휘 인원 ({len(potential_risk)}명)")
            st.write("역량은 우수하나 성과가 정체된 인원입니다. 업무 배치나 환경 점검이 필요합니다.")
            st.dataframe(potential_risk[['사번', '성명', '부서', '직급', '역량점수', '성과점수']])

        with col_risk2:
            if '전년도총점' in df.columns:
                st.warning(f"성과 급락 인원 ({len(warning_drop)}명)")
                st.write("전년 대비 10점 이상 하락한 인원입니다. 면담 및 코칭을 권장합니다.")
                st.dataframe(warning_drop[['사번', '성명', '부서', '직급', '총점', '점수차이']])
            else:
                st.info("전년도 데이터를 입력하면 성적 급락자 추적이 가능합니다.")

        st.divider()

        # 3. 부서별 성과 격차 (Deviation)
        st.subheader("부서별 성과 편차 분석")
        # 편차가 크다는 것은 부서 내 실력 차이가 극심함을 의미
        dept_std = df.groupby('부서')['총점'].std().sort_values(ascending=False).reset_index()
        fig_std = px.bar(dept_std, x='부서', y='총점', title="부서 내 성과 불균형(표준편차)",
                         labels={'총점': '점수 편차'}, template='plotly_white')
        st.plotly_chart(fig_std, width='stretch')

    with tab8:
        st.subheader("조직 인재 밀도 및 성장 엔진 분석")
        st.caption("부서별 고성과자 비중과 근속 구간별 성과 기여도를 분석합니다.")

        # 1. 부서별 인재 밀도 (S/A 등급 비중)
        # 전체 인원 중 S 또는 A 등급의 비율 계산
        dept_total = df.groupby('부서').size()
        dept_stars = df[df['종합등급'].isin(['S', 'A'])].groupby('부서').size()
        talent_density = (dept_stars / dept_total * 100).fillna(0).sort_values(ascending=False).reset_index()
        talent_density.columns = ['부서', '고성과자 비중(%)']

        col_engine1, col_engine2 = st.columns(2)

        with col_engine1:
            st.write("**부서별 인재 밀도 (S/A등급 비율)**")
            fig_density = px.bar(talent_density, x='부서', y='고성과자 비중(%)',
                                 color='고성과자 비중(%)', color_continuous_scale='Greens',
                                 text_auto='.1f', template='plotly_white')
            st.plotly_chart(fig_density, width='stretch')

        with col_engine2:
            # 2. 근속 구간별 성과 분포 (Binning)
            bins = [0, 2, 5, 10, 20, 100]
            labels = ['1-2년(신입)', '3-5년(주니어)', '6-10년(시니어)', '11-20년(베테랑)', '20년 이상']
            df['근속구간'] = pd.cut(df['근무기간'], bins=bins, labels=labels)

            tenure_perf = df.groupby('근속구간', observed=True)['총점'].mean().reset_index()

            st.write("**⏳ 근속 구간별 평균 성과**")
            fig_tenure = px.line(tenure_perf, x='근속구간', y='총점', markers=True,
                                 title="근속 기간에 따른 성과 성장 곡선", template='plotly_white')
            st.plotly_chart(fig_tenure, width='stretch')

        st.divider()

        # 3. 직급별 역량 vs 성과 밸런스 (Radar Chart 대용 Bar)
        st.subheader("직급별 역량-성과 밸런스")
        rank_balance = df.groupby('직급', observed=True)[['역량점수', '성과점수']].mean().reset_index()

        # 데이터를 긴 형식(Long format)으로 변환
        rank_balance_melted = rank_balance.melt(id_vars='직급', var_name='평가항목', value_name='점수')

        fig_balance = px.bar(rank_balance_melted, x='직급', y='점수', color='평가항목', barmode='group',
                             category_orders={'직급': rank_order},
                             color_discrete_map={'역량점수': '#636EFA', '성과점수': '#EF553B'},
                             template='plotly_white')
        st.plotly_chart(fig_balance, width='stretch')
        st.info("직급이 높아질수록 역량과 성과 점수가 균형 있게 동반 상승하는 것이 이상적입니다.")

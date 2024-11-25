import streamlit as st
import pandas as pd
import fuzzywuzzy
from fuzzywuzzy import fuzz
import seaborn as sns

st.set_page_config(
    page_title="Analyse des fusions perlées",
    page_icon=":bar_chart:",
    layout="wide"
)

fusions = st.file_uploader("Choisir un fichier de fusions.")
if fusions is not None:
    fusions['group']=fusions['group'].astype(str)
    fusions['stop_area_names']=fusions['stop_area_name'].astype(str)
    number_of_stops = st.number_input("Nombre d'arrêts dans le groupe",0,100,20,1)
    group_to_analyse=st.text_input("Group à analyser")
    groups_with_more_than_n_stops = fusions.groupby('group').filter(lambda x: len(x) > number_of_stops)
    df_grouped = fusions[fusions.group==group_to_analyse]
    names_group = pd.DataFrame(columns=['names'], data = df_grouped.stop_area_name.unique().tolist())
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("- Nb de zones d'arrêt par groupe")
        st.dataframe(groups_with_more_than_n_stops['group'].value_counts())
    with col2:
        st.markdown("- Groupe à analyser (" + str(df_grouped.shape[0]) + " zones d'arrêts)")
        st.dataframe(df_grouped)
    with col3:
        st.markdown("- Noms du groupe (" + str(names_group.shape[0]) + " noms différents)")
        st.dataframe(names_group)
    stop_point_names_ct = pd.crosstab(names_group['names'], names_group['names']).apply(lambda col: [fuzz.ratio(col.name, x) for x in col.index])
    st.markdown("- Similitudes entre les noms")
    heatmap_plot=st.radio("Affichage de la heatmap", ['Heatmap complète', 'Ratio maximal'])
    if heatmap_plot=='Ratio maximal':
        ratio = st.number_input("Ratio maximal",0,100,20,1)
        for i in stop_point_names_ct.columns:
            data_to_plot = stop_point_names_ct[stop_point_names_ct[i] >ratio][i].drop([i], axis=0)
        annotation=True
    else:
        data_to_plot = stop_point_names_ct.copy()
        annotation=False
    #st.dataframe(stop_point_names_ct)
    annotation = st.checkbox('Affichage des valeurs de similtude (/!\ moins de 20 noms pour un affichage clair)')
    plot = sns.heatmap(stop_point_names_ct, annot=annotation)
    st.pyplot(plot.get_figure())
    with st.expander("Analyse de toute la donnée"):
        st.dataframe(fusions['group'].value_counts())
else:
    st.error("Veuillez choisir un fichier de fusions.", icon="🚨")
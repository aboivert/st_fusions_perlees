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
st.markdown("- Ajouter nombre de noms uniques par groupe")
st.markdown("- Distance entre zones d'arrêts avec nom unique")
st.markdown("- Zones des distances entre barycentres")
col__1, col__2 = st.columns(2)
with col__1:
    fusions_file = st.file_uploader("Choisir un fichier de fusions.")   
with col__2:
    stops_file = st.file_uploader("Choisir le fichier stops.txt du NTFS avant fusion correspondant au fichier de fusions.")
#fusions_file = pd.read_csv(r"C:\Users\aboivert\Downloads\export-merge_081124.csv")
#stops_files = pd.read_csv(r"C:\Users\aboivert\Downloads\stops.txt")
if fusions_file is not None:
    fusions = pd.read_csv(fusions_file)
    stops = pd.read_csv(stops_file)
    #stops = pd.read_csv(r"C:\Users\aboivert\Downloads\stops.txt")
    #fusions = pd.read_csv(r"C:\Users\aboivert\Downloads\export-merge_081124.csv")
    fusions['group']=fusions['group'].astype(str)
    fusions['stop_area_names']=fusions['stop_area_name'].astype(str)
    number_of_stops = st.number_input("Nombre d'arrêts dans le groupe",0,100,20,1)
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        analyse_groupe = st.checkbox("Analyse par groupe", False)
    if analyse_groupe:
        with col_2:
            group_to_analyse=st.text_input("Group à analyser")
        with col_3:
            analyse_stops = st.checkbox("Analyse des distances entre zones d'arrêts", False)
    groups_with_more_than_n_stops = fusions.groupby('group').filter(lambda x: len(x) > number_of_stops)
    if analyse_groupe:
        df_grouped = fusions[fusions.group==group_to_analyse]
        names_group = pd.DataFrame(columns=['names'], data = df_grouped.stop_area_name.unique().tolist())
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("- Nb de zones d'arrêt par groupe")
            st.dataframe(groups_with_more_than_n_stops['group'].value_counts())
        with col2:
            st.markdown("- Groupe à analyser (" + str(df_grouped.shape[0]) + " zones d'arrêts)")
            if df_grouped.empty:
                st.error("Groupe inexistant. Vérifier la case 'Group à analyser'")
            else:
                st.dataframe(df_grouped)
        with col3:
            st.markdown("- Noms du groupe (" + str(names_group.shape[0]) + " noms différents)")
            if df_grouped.empty:
                st.error("Groupe inexistant. Vérifier la case 'Group à analyser'")
            else:
                st.dataframe(names_group)
    else:
        st.markdown("- Nb de zones d'arrêt par groupe")
        st.dataframe(groups_with_more_than_n_stops['group'].value_counts())     
    with st.expander("Analyse de similitude entre noms uniques"):
        if analyse_groupe:  
            stop_point_names_ct = pd.crosstab(names_group['names'], names_group['names']).apply(lambda col: [fuzz.ratio(col.name, x) for x in col.index])
            st.markdown("- Similitudes entre les noms")
            #heatmap_plot=st.radio("Affichage de la heatmap", ['Heatmap complète', 'Ratio maximal'])
            #if heatmap_plot=='Ratio maximal':
            #    ratio = st.number_input("Ratio maximal",0,100,20,1)
            #    for i in stop_point_names_ct.columns:
            #        data_to_plot = stop_point_names_ct[stop_point_names_ct[i] >ratio][i].drop([i], axis=0)
            #else:
            #    data_to_plot = stop_point_names_ct.copy()
            #st.dataframe(stop_point_names_ct)
            annotation = st.checkbox('Affichage des valeurs de similtude')
            if names_group.shape[0]>20:
                st.warning("Il y a plus de 20 noms différents. L'affichage peut ne pas être clair.")
            try:
                plot = sns.heatmap(stop_point_names_ct, annot=annotation)
                st.pyplot(plot.get_figure())
            except: 
                st.error("Groupe inexistant. Vérifier la case 'Group à analyser'")
    if analyse_stops:
        with st.expander("Analyse entre zones d'arrêts avec le même nom"):
            st.text("Permet de vérifier pour chacun des " + str(names_group.shape[0]) + " noms uniques du groupe " + str(group_to_analyse) +  " si toutes les zones d'arrêts définis avec ce nom sont bien proches entre elles.")
            if stops.empty:
                st.error("Le fichier stops est vide. L'analyse est impossible.")
        with st.expander("Analyse de distance entre zones d'arrêt"):
            st.text("Test")
    with st.expander("Analyse de toute la donnée"):
        st.dataframe(fusions['group'].value_counts())
else:
    st.error("Veuillez choisir un fichier de fusions.", icon="🚨")

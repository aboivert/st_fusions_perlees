import streamlit as st
import pandas as pd
import fuzzywuzzy
from fuzzywuzzy import fuzz
import seaborn as sns
import numpy as np
import pydeck

def compute_distance(lat_pt, lon_pt, lat_bary, lon_bary):
    earth_radius = 6371e3
    phi_pt = lat_pt * np.pi/180
    phi_bary = lat_bary * np.pi/180
    delta_phi = (lat_bary - lat_pt) * np.pi/180
    delta_lambda = (lon_bary - lon_pt) * np.pi/180
    a = np.sin(delta_phi/2) * np.sin(delta_phi/2) + np.cos(phi_pt) * np.cos(phi_bary) * np.sin(delta_lambda/2) * np.sin(delta_lambda/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return earth_radius*c

st.set_page_config(
    page_title="Analyse des fusions perlées",
    page_icon=":bar_chart:",
    layout="wide"
)
st.markdown("- Ajouter nombre de noms uniques par groupe")
st.markdown("- Couleurs + barycentre et vérif Ethiopie")
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
    analyse_stops=False
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
            #st.text("Permet de vérifier pour chacun des " + str(names_group.shape[0]) + " noms uniques du groupe " + str(group_to_analyse) +  " si toutes les zones d'arrêts définis avec ce nom sont bien proches entre elles.")
            if stops.empty:
                st.error("Le fichier stops est vide. L'analyse est impossible.")
            else:
                stops = stops[stops.location_type==1]
                barycentre_df = pd.DataFrame()
                for index, row in names_group.iterrows():
                    temp_data = stops[stops.stop_name==names_group.loc[index].names]
                    temp_data['problem'] = 0
                    temp_data['dist'] = 0
                    mean_lat = temp_data.stop_lat.mean()
                    mean_lon = temp_data.stop_lon.mean()
                    new_row={'nom':names_group.loc[index].names,'mean_lat':mean_lat,'mean_lon':mean_lon}
                    barycentre_df = barycentre_df._append(new_row, ignore_index=True)
                    long_distances = pd.DataFrame()
                    for index1, row1 in temp_data.iterrows():
                        temp_dist = compute_distance(temp_data.loc[index1].stop_lat, temp_data.loc[index1].stop_lon, mean_lat, mean_lon)
                        if temp_dist > 100:
                            temp_data.loc[index1,'problem'] = 1
                            #st.text("Le stop ID " + str(temp_data.loc[index1].stop_id) + " est placé loin du barycentre correspondant aux arrêts nommés " + str(temp_data.loc[index1].stop_name) + " (" + str(temp_dist) + " mètres).")
                        #else:
                        #    temp_data.loc[index1,'problem'] = '[0, 255, 0]'
                        temp_data.loc[index1,'dist'] = temp_dist
                    if (temp_data.problem==1).any():
                        st.text("Zone d'arrêt " + str(temp_data.loc[index1].stop_name))
                        st.dataframe(temp_data[['stop_id','stop_name','stop_lat','stop_lon','problem','dist']])
                        #st.map(temp_data, latitude='stop_lat',longitude='stop_lon')
                        point_layer = pydeck.Layer(
                            "ScatterplotLayer",
                            data=temp_data,
                            #id="capital-cities",
                            get_position=["stop_lon", "stop_lat"],
                            get_color="[255,255, 0]",
                            pickable=True,
                            auto_highlight=True,
                            get_radius=50,
                        )
                        view_state = pydeck.ViewState(
                            latitude=temp_data.stop_lat.mean(), longitude=temp_data.stop_lon.mean(), controller=True, zoom=5 , pitch=30
                        )
                        chart = pydeck.Deck(
                            point_layer,
                            initial_view_state=view_state,
                            tooltip={"text": "{stop_name} ({stop_id})"},
                        )
                        event = st.pydeck_chart(chart, on_select="rerun", selection_mode="multi-object")
                        #st.text("Imrpimer la carte")
                        #st.text(temp_data.loc[index1].stop_name)
                        #st.dataframe(temp_data)
                        #Print la carte avec bary loin et ok
                #st.dataframe(barycentre_df)
                #Print barycenter df
        with st.expander("Analyse de distance entre zones d'arrêt"):
            barycentre_df2 = pd.DataFrame()
            for index2, row2 in names_group.iterrows():
                temp_data = stops[stops.stop_name==names_group.loc[index2].names]
                mean_lat = temp_data.stop_lat.mean()
                mean_lon = temp_data.stop_lon.mean()
                new_row={'nom':names_group.loc[index2].names,'mean_lat':mean_lat,'mean_lon':mean_lon}
                barycentre_df2 = barycentre_df2._append(new_row, ignore_index=True)  
            #st.dataframe(barycentre_df2)
            point_layer = pydeck.Layer(
                "ScatterplotLayer",
                data=barycentre_df2,
                #id="capital-cities",
                get_position=["mean_lon", "mean_lat"],
                get_color="[255, 75, 75]",
                pickable=True,
                auto_highlight=True,
                get_radius=50,
            )
            view_state = pydeck.ViewState(
                latitude=barycentre_df2.mean_lat.mean(), longitude=barycentre_df2.mean_lon.mean(), controller=True, zoom=10 , pitch=30
            )
            chart = pydeck.Deck(
                point_layer,
                initial_view_state=view_state,
                tooltip={"text": "{nom}"},
            )
            event = st.pydeck_chart(chart, on_select="rerun", selection_mode="multi-object")
            st.dataframe(barycentre_df2)
    with st.expander("Analyse de toute la donnée"):
        st.dataframe(fusions['group'].value_counts())
else:
    st.error("Veuillez choisir un fichier de fusions.", icon="🚨")

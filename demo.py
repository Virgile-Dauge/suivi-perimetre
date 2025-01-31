import streamlit as st
import pandas as pd
import io

# Charger les données initiales
# data = {
#     "PRM": [],
#     "Nom du site": [],
#     "Segment": [],
#     "FTA": [],
#     "OFFRE": [],
#     "PS": [],
#     "POINTE": [],
#     "HPH": [],
#     "HCH": [],
#     "HPB": [],
#     "HCB": [],
#     "Date début de fourniture": [],
#     "Date fin de fourniture": [],
#     "Regroupement": [],
#     "Moyen de paiement": [],
#     "Numéro d'engagement Chorus": [],
#     "Code Service Chorus": [],
#     "Numéro SIRET": [],
#     "Contact": [],
#     "Téléphone": [],
#     "Adresse email": [],
#     "Branchement provisoire": [],
#     "Commentaire": [],
#     "Statut": [],
# }
# df = pd.DataFrame(data)

# Fonction pour appliquer les couleurs en fonction du statut
def highlight_status(row):
    if row["Statut"] == "Réalisé":
        return ["background-color: lightgreen"] * len(row)
    elif row["Statut"] in ["Résilié", "Non réalisé"]:
        return ["background-color: lightcoral"] * len(row)
    elif row["Statut"] == "En attente":
        return ["background-color: lightyellow"] * len(row)
    else:
        return [""] * len(row)

# Titre de l'application
st.title("Suivi des demandes GRD")

# Initialisation de la session
if "df" not in st.session_state:
    st.session_state["df"] = pd.read_csv('base.csv')
if "filtered_df" not in st.session_state:
    st.session_state["filtered_df"] = st.session_state["df"].copy()
if "filters" not in st.session_state:
    # st.session_state["filters"] = {col: "" for col in st.session_state["df"].columns}
    st.session_state["filters"] = {col: '' for col  in ['PRM', 'Nom du site', 'Segment', 'Statut']}
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = set()

# Ajout des filtres dans des widgets de filtre
with st.sidebar:
    st.header("Filtres")
    # for column in st.session_state["df"].columns:
    for column in st.session_state["filters"]:
        st.session_state["filters"][column] = st.text_input(f"Filtrer par {column}", key=f"filter_{column}")
    
    # Appliquer les filtres dynamiquement
    filtered_df = st.session_state["df"].copy()
    for column, value in st.session_state["filters"].items():
        if value:
            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False, na=False)]
    st.session_state["filtered_df"] = filtered_df

# Affichage du tableau avec mise en couleur
st.dataframe(st.session_state["filtered_df"].style.apply(highlight_status, axis=1))

# Ajouter une ligne
with st.expander("Ajouter une demande GRD à traiter"):
    with st.form("add_row_form"):
        new_row = {}
        for column in st.session_state["df"].columns:
            if column not in ["Statut"]:
                new_row[column] = st.text_input(f"Valeur pour {column}", "")
        new_row["Statut"] = "Demande GRD à traiter"
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            st.session_state["df"] = pd.concat([st.session_state["df"], pd.DataFrame([new_row])], ignore_index=True)
            st.session_state["filtered_df"] = st.session_state["df"].copy()
            st.success("Nouvelle ligne ajoutée avec succès !")
            st.rerun()

# Exporter le tableau en XLSX
st.subheader("Exportation")
output = io.BytesIO()
st.session_state["df"].to_excel(output, index=False, sheet_name="Raccordements", engine="openpyxl")
output.seek(0)

st.download_button(
    label="Exporter en XLSX",
    data=output,
    file_name="tableau_raccordements.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# Importer des données
st.subheader("Importer des lignes")
uploaded_file = st.file_uploader("Importer un ou plusieurs fichiers Excel ou CSV", type=["xlsx"], accept_multiple_files=True)
to_read = [f for f in uploaded_file if f.name not in st.session_state["uploaded_files"]]
if to_read:
    dataframes = [pd.read_excel(f).drop(columns=[col for col in pd.read_excel(f, nrows=0).columns if col.startswith('Unnamed')], errors='ignore').assign(Statut="Demande GRD à traiter") for f in to_read]
    st.session_state["df"] = pd.concat(dataframes + [st.session_state["df"]], ignore_index=True)
    st.session_state["uploaded_files"].update(f.name for f in to_read)
    st.success(f"Données importées avec succès !")
    st.rerun()

# Supprimer les lignes
st.subheader("Supprimer des lignes")
if not st.session_state["df"].empty and "PRM" in st.session_state["df"].columns:
    selection_mapping = {f"{row['PRM']}": index for index, row in st.session_state["df"].iterrows() if row['Statut']=="Demande GRD à traiter"}
    options = list(selection_mapping.keys())
else:
    selection_mapping = {}
    options = []

lines_to_delete = st.multiselect("Sélectionnez les lignes à supprimer", options)

if st.button("Supprimer les lignes sélectionnées"):
    indices_to_delete = [selection_mapping[prm] for prm in lines_to_delete if prm in selection_mapping]
    st.session_state["df"] = st.session_state["df"].drop(indices_to_delete).reset_index(drop=True)
    st.session_state["filtered_df"] = st.session_state["df"].copy()
    st.success("Lignes supprimées avec succès !")
    st.rerun()

# Indicateur
st.subheader("Indicateur")
st.metric(label="Indicateur de flexibilité du périmètre au 01/01/2025", value="+3.2%")

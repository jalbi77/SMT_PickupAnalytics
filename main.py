from datetime import datetime
import streamlit as st
import plotly.express as px
from analysis import calculate, SPECS
from data import load_data


def main():
    st.set_page_config(page_title='SMT Pickup Analytics', page_icon='🏭', layout='wide')
    st.title('SMT Pickup Analytics')
    st.write('Bauteile für Continuous Improvement sowie Feeder und Saugdüsen für die Instandhaltung bewerten.')
    st.info('Vorläufige historische Gewichtungen: Der Fehlerindex ist keine Fehlerquote und keine Wartungsprognose. Kleine Stichproben gesondert beurteilen.')
    if st.button('Daten laden / aktualisieren'):
        try:
            with st.spinner('Lese profiler …'):
                device, nozzle = load_data()
                results = {name: calculate(nozzle if name == 'Saugdüsen' else device, name)
                           for name in SPECS}
            st.session_state['results'] = results
            st.session_state['loaded_at'] = datetime.now().astimezone().isoformat(timespec='seconds')
            st.session_state.pop('load_failed', None)
        except Exception as exc:
            st.session_state['load_failed'] = type(exc).__name__
    if 'load_failed' in st.session_state:
        st.error(f"Laden fehlgeschlagen ({st.session_state['load_failed']}). Netzwerk, ODBC-Treiber und lokale Nexim-Konfiguration prüfen.")
        if 'results' in st.session_state:
            st.warning('Die letzte erfolgreiche Datenbasis bleibt sichtbar und wurde nicht aktualisiert.')
    if 'results' not in st.session_state:
        st.write('Daten laden, um die Auswertung zu starten. Quelle: ausschliesslich profiler.')
        return
    st.caption(f"Abruf: {st.session_state['loaded_at']} · kein Produktionszeitraumfilter")
    for name, (frame, missing) in st.session_state['results'].items():
        key, denominator, weights = SPECS[name]
        st.header(name)
        st.caption('Gewichte RejectParts / NoPickupCount / PickupErrors / VisionErrors: ' + ' / '.join(map(str, weights)))
        if missing:
            st.warning(f'{missing} Quellzeilen ohne Kennung wurden ausgeschlossen.')
        top = frame.loc[frame['Status'] == 'Bewertbar'].head(10)
        if top.empty:
            st.info('Keine bewertbaren Daten vorhanden.')
        else:
            fig = px.scatter(top, x=denominator, y='ErrorIndex', text=key,
                             size='WeightedErrors', hover_data=['UnweightedErrors'],
                             labels={'ErrorIndex': 'Gewichteter Fehlerindex', denominator: denominator},
                             title='Top 10 nach gewichtetem Fehlerindex')
            st.plotly_chart(fig, width='stretch')
        with st.expander('Alle Einheiten und ungewichtete Fehlerzahlen'):
            st.dataframe(frame, hide_index=True)


if __name__ == '__main__':
    main()

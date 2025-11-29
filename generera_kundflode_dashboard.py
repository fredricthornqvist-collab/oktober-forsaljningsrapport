#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generera HTML Dashboard för Kundflöde med Fortnox-styling
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def ladda_nya_kunder_data(filpath):
    """Ladda och förbered data för nya kunder."""
    df = pd.read_csv(filpath)
    
    # Rensa numeriska kolumner
    df['Nya kunder'] = pd.to_numeric(df['Nya kunder'], errors='coerce').fillna(0).astype(int)
    
    # Separera år och månad
    df['År'] = df['ÅrMånad'] // 100
    df['Månad'] = df['ÅrMånad'] % 100
    
    # Gruppera anskaffningskanaler
    def kategorisera_kanal(kanal):
        if pd.isna(kanal) or kanal == '-':
            return 'övrigt'
        kanal_lower = str(kanal).lower()
        if 'fortnox.se' in kanal_lower or 'fortnox se' in kanal_lower:
            return 'fortnox.se'
        elif 'fortnox' in kanal_lower and 'fortnox.se' not in kanal_lower:
            return 'fortnox'
        elif 'winback' in kanal_lower:
            return 'winback'
        elif 'byrå' in kanal_lower:
            return 'byrå'
        elif 'cling' in kanal_lower or 'boardeaser' in kanal_lower or 'okänd' in kanal_lower:
            return 'övrigt'
        else:
            return 'övrigt'
    
    df['Anskaffningskanal'] = df['Anskaffad via - Detalj'].apply(kategorisera_kanal)
    
    return df


def ladda_kundstock_data(filpath_2024, filpath_2025):
    """Ladda och kombinera kundstock för 2024 och 2025."""
    df_2024 = pd.read_csv(filpath_2024)
    df_2025 = pd.read_csv(filpath_2025)
    
    # Lägg till år-information
    df_2024['År'] = 2024
    df_2025['År'] = 2025
    
    # Kombinera
    df = pd.concat([df_2024, df_2025], ignore_index=True)
    
    # Rensa numeriska kolumner
    df['Antal kunder'] = pd.to_numeric(df['Antal kunder'], errors='coerce').fillna(0).astype(int)
    
    # Separera månad från ÅrMånad
    df['Månad'] = df['ÅrMånad'] % 100
    
    return df


def ladda_kundmål_data(filpath):
    """Ladda och förbered kundmål."""
    df = pd.read_csv(filpath)
    
    # Mappa månadsnamn till nummer
    månad_map = {
        'Jan': 1, 'Feb': 2, 'Mars': 3, 'Apr': 4, 'Maj': 5, 'Juni': 6,
        'Juli': 7, 'Aug': 8, 'Sep': 9, 'Okt': 10, 'Nov': 11, 'Dec': 12
    }
    df['Månad'] = df['Månad'].map(månad_map)
    
    # Rensa numeriska kolumner (non-breaking spaces)
    def rensa_nummer(värde):
        if pd.isna(värde):
            return 0
        if isinstance(värde, (int, float)):
            return int(värde)
        return int(str(värde).replace('\xa0', '').replace(' ', '').replace(',', ''))
    
    df['Byrå'] = df['Byrå'].apply(rensa_nummer)
    df['Winback'] = df['Winback'].apply(rensa_nummer)
    df['säljare'] = df['säljare'].apply(rensa_nummer)
    df['fortnox.se'] = df['fortnox.se'].apply(rensa_nummer)
    df['Cling/Boardeaser/Okänt'] = df['Cling/Boardeaser/Okänt'].apply(rensa_nummer)
    df['Totalt'] = df['Totalt'].apply(rensa_nummer)
    
    # Omforma till long format med kanal-kategorier
    mål_data = []
    for _, row in df.iterrows():
        månad = row['Månad']
        mål_data.append({'Månad': månad, 'Kanal': 'byrå', 'Mål': row['Byrå']})
        mål_data.append({'Månad': månad, 'Kanal': 'winback', 'Mål': row['Winback']})
        mål_data.append({'Månad': månad, 'Kanal': 'fortnox', 'Mål': row['säljare']})
        mål_data.append({'Månad': månad, 'Kanal': 'fortnox.se', 'Mål': row['fortnox.se']})
        mål_data.append({'Månad': månad, 'Kanal': 'övrigt', 'Mål': row['Cling/Boardeaser/Okänt']})
        mål_data.append({'Månad': månad, 'Kanal': 'alla', 'Mål': row['Totalt']})
    
    return pd.DataFrame(mål_data)


def filtrera_period(df, år, månad):
    """Filtrera data för en specifik period."""
    return df[(df['År'] == år) & (df['Månad'] == månad)].copy()


def filtrera_kanal(df, kanal):
    """Filtrera nya kunder för en specifik anskaffningskanal."""
    if kanal == 'alla':
        return df
    return df[df['Anskaffningskanal'] == kanal].copy()


def beräkna_nya_kunder_kpi(df):
    """Beräkna KPI:er för nya kunder."""
    return {
        'Nya kunder': int(df['Nya kunder'].sum()),
    }


def beräkna_kundstock_kpi(df):
    """Beräkna KPI:er för kundstock."""
    return {
        'Total kundstock': int(df['Antal kunder'].sum()),
    }


def jämför_perioder(kpi_aktuell, kpi_jämförelse):
    """Jämför två perioder och returnera förändringarna."""
    jämförelse = {}
    
    for nyckel in kpi_aktuell.keys():
        värde_aktuell = kpi_aktuell[nyckel]
        värde_jämförelse = kpi_jämförelse.get(nyckel, 0)
        
        förändring = värde_aktuell - värde_jämförelse
        
        if värde_jämförelse > 0:
            förändring_procent = ((värde_aktuell - värde_jämförelse) / värde_jämförelse) * 100
        else:
            förändring_procent = 0 if värde_aktuell == 0 else 100
        
        jämförelse[nyckel] = {
            'Aktuell': värde_aktuell,
            'Jämförelse': värde_jämförelse,
            'Förändring': förändring,
            'Förändring%': förändring_procent,
        }
    
    return jämförelse


def generera_kpi_card_kombinerad(titel, värde_aktuell, värde_yoy, värde_mom, 
                                 förändr_yoy, förändr_mom, förändr_yoy_pct, förändr_mom_pct,
                                 månad=10, år=2025, mål=None):
    """Generera HTML för ett kombinerat KPI-kort med både YoY och MoM samt mål."""
    
    månadsnamn = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Maj", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dec"
    }
    
    mom_månad = 12 if månad == 1 else månad - 1
    mom_år = år - 1 if månad == 1 else år
    yoy_år = år - 1
    
    värde_text = f"{int(värde_aktuell):,}"
    yoy_text = f"vs {månadsnamn[månad]} {yoy_år}: {int(värde_yoy):,}"
    mom_text = f"vs {månadsnamn[mom_månad]} {mom_år}: {int(värde_mom):,}"
    
    yoy_förändring_text = f"{förändr_yoy_pct:+.1f}% ({förändr_yoy:+,})"
    mom_förändring_text = f"{förändr_mom_pct:+.1f}% ({förändr_mom:+,})"
    
    yoy_positiv = förändr_yoy > 0
    mom_positiv = förändr_mom > 0
    
    yoy_pil = "↑" if yoy_positiv else "↓" if förändr_yoy < 0 else "→"
    yoy_färg = "positive" if yoy_positiv else "negative" if förändr_yoy < 0 else "neutral"
    
    mom_pil = "↑" if mom_positiv else "↓" if förändr_mom < 0 else "→"
    mom_färg = "positive" if mom_positiv else "negative" if förändr_mom < 0 else "neutral"
    
    # Lägg till målrad om mål finns
    mål_html = ""
    if mål is not None and mål > 0:
        uppfyllelse = (värde_aktuell / mål) * 100
        mål_diff = värde_aktuell - mål
        mål_uppnått = uppfyllelse >= 100
        mål_pil = "✓" if mål_uppnått else "✗"
        mål_färg = "positive" if mål_uppnått else "negative"
        mål_html = f"""
            <div class="comparison-row">
                <span class="comparison-label">Mål:</span>
                <span class="comparison-value">{int(mål):,}</span>
                <span class="kpi-change-inline {mål_färg}">
                    <span class="arrow-small">{mål_pil}</span>
                    {uppfyllelse:.1f}% ({mål_diff:+,})
                </span>
            </div>"""
    
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{titel}</div>
        <div class="kpi-value">{värde_text}</div>
        <div class="kpi-comparisons">
            <div class="comparison-row">
                <span class="comparison-label">YoY:</span>
                <span class="comparison-value">{yoy_text}</span>
                <span class="kpi-change-inline {yoy_färg}">
                    <span class="arrow-small">{yoy_pil}</span>
                    {yoy_förändring_text}
                </span>
            </div>
            <div class="comparison-row">
                <span class="comparison-label">MoM:</span>
                <span class="comparison-value">{mom_text}</span>
                <span class="kpi-change-inline {mom_färg}">
                    <span class="arrow-small">{mom_pil}</span>
                    {mom_förändring_text}
                </span>
            </div>{mål_html}
        </div>
    </div>
    """


def sortera_omsättningsintervall(intervall_str):
    """Extrahera start-värde från omsättningsintervall för sortering."""
    import re
    intervall_str = str(intervall_str).strip()
    
    # Hantera specialfall
    if intervall_str.startswith('< '):
        return 0
    if intervall_str.startswith('> '):
        return 99999999
    
    # Extrahera första numret från strängar som "1 - 49 tkr", "1000 - 2499 tkr"
    match = re.match(r'(\d+)', intervall_str.replace(',', '').replace(' ', ''))
    if match:
        return int(match.group(1))
    
    # Om inget nummer hittas, returnera högt värde för att hamna sist
    return 999999999


def analysera_dimension_nya_kunder(df_aktuell, df_yoy, df_mom, dimension, top_n=10):
    """Analysera en dimension för nya kunder med YoY och MoM."""
    
    # Filtrera bort "Okänd" och "Okänt" för SNI, Omsättningsintervall och Antal anställda
    if dimension in ['SNI', 'Omsättningsintervall', 'Antal anställda']:
        df_aktuell = df_aktuell[~df_aktuell[dimension].isin(['Okänd', 'Okänt'])].copy()
        df_yoy = df_yoy[~df_yoy[dimension].isin(['Okänd', 'Okänt'])].copy()
        df_mom = df_mom[~df_mom[dimension].isin(['Okänd', 'Okänt'])].copy()
    
    # Aktuell period
    aktuell = df_aktuell.groupby(dimension).agg({
        'Nya kunder': 'sum'
    }).reset_index()
    
    # YoY
    yoy = df_yoy.groupby(dimension).agg({
        'Nya kunder': 'sum'
    }).reset_index()
    yoy = yoy.rename(columns={'Nya kunder': 'Nya kunder_yoy'})
    
    # MoM
    mom = df_mom.groupby(dimension).agg({
        'Nya kunder': 'sum'
    }).reset_index()
    mom = mom.rename(columns={'Nya kunder': 'Nya kunder_mom'})
    
    # Slå ihop
    result = aktuell.merge(yoy, on=dimension, how='left').merge(mom, on=dimension, how='left')
    result = result.fillna(0)
    
    # Beräkna förändringar
    result['YoY_diff'] = result['Nya kunder'] - result['Nya kunder_yoy']
    result['MoM_diff'] = result['Nya kunder'] - result['Nya kunder_mom']
    
    result['YoY%'] = result.apply(
        lambda row: ((row['Nya kunder'] - row['Nya kunder_yoy']) / row['Nya kunder_yoy'] * 100) 
        if row['Nya kunder_yoy'] > 0 else (100 if row['Nya kunder'] > 0 else 0),
        axis=1
    )
    
    result['MoM%'] = result.apply(
        lambda row: ((row['Nya kunder'] - row['Nya kunder_mom']) / row['Nya kunder_mom'] * 100) 
        if row['Nya kunder_mom'] > 0 else (100 if row['Nya kunder'] > 0 else 0),
        axis=1
    )
    
    # Sortera och begränsa
    if dimension == 'Omsättningsintervall':
        # Sortera omsättningsintervall efter numeriskt värde
        result['_sort_key'] = result[dimension].apply(sortera_omsättningsintervall)
        result = result.sort_values('_sort_key').drop('_sort_key', axis=1).head(top_n)
    else:
        result = result.sort_values('Nya kunder', ascending=False).head(top_n)
    
    return result


def analysera_dimension_kundstock(df_aktuell, df_yoy, df_mom, dimension, top_n=10):
    """Analysera en dimension för kundstock med YoY och MoM."""
    
    # Filtrera bort "Okänd" och "Okänt" för SNI, Omsättningsintervall och Antal anställda
    if dimension in ['SNI', 'Omsättningsintervall', 'Antal anställda']:
        df_aktuell = df_aktuell[~df_aktuell[dimension].isin(['Okänd', 'Okänt'])].copy()
        df_yoy = df_yoy[~df_yoy[dimension].isin(['Okänd', 'Okänt'])].copy()
        df_mom = df_mom[~df_mom[dimension].isin(['Okänd', 'Okänt'])].copy()
    
    # Aktuell period
    aktuell = df_aktuell.groupby(dimension).agg({
        'Antal kunder': 'sum'
    }).reset_index()
    
    # YoY
    yoy = df_yoy.groupby(dimension).agg({
        'Antal kunder': 'sum'
    }).reset_index()
    yoy = yoy.rename(columns={'Antal kunder': 'Antal kunder_yoy'})
    
    # MoM
    mom = df_mom.groupby(dimension).agg({
        'Antal kunder': 'sum'
    }).reset_index()
    mom = mom.rename(columns={'Antal kunder': 'Antal kunder_mom'})
    
    # Slå ihop
    result = aktuell.merge(yoy, on=dimension, how='left').merge(mom, on=dimension, how='left')
    result = result.fillna(0)
    
    # Beräkna förändringar
    result['YoY_diff'] = result['Antal kunder'] - result['Antal kunder_yoy']
    result['MoM_diff'] = result['Antal kunder'] - result['Antal kunder_mom']
    
    result['YoY%'] = result.apply(
        lambda row: ((row['Antal kunder'] - row['Antal kunder_yoy']) / row['Antal kunder_yoy'] * 100) 
        if row['Antal kunder_yoy'] > 0 else (100 if row['Antal kunder'] > 0 else 0),
        axis=1
    )
    
    result['MoM%'] = result.apply(
        lambda row: ((row['Antal kunder'] - row['Antal kunder_mom']) / row['Antal kunder_mom'] * 100) 
        if row['Antal kunder_mom'] > 0 else (100 if row['Antal kunder'] > 0 else 0),
        axis=1
    )
    
    # Sortera och begränsa
    if dimension == 'Omsättningsintervall':
        # Sortera omsättningsintervall efter numeriskt värde
        result['_sort_key'] = result[dimension].apply(sortera_omsättningsintervall)
        result = result.sort_values('_sort_key').drop('_sort_key', axis=1).head(top_n)
    else:
        result = result.sort_values('Antal kunder', ascending=False).head(top_n)
    
    return result


def generera_tabell_nya_kunder(titel, df, dimension_namn, max_rader=10):
    """Generera HTML-tabell för nya kunder."""
    
    if len(df) == 0:
        return f"""
        <div class="table-container">
            <h3 class="table-title">{titel}</h3>
            <p style="text-align: center; color: #6B7280; padding: 2rem;">Ingen data tillgänglig</p>
        </div>
        """
    
    df = df.head(max_rader)
    
    rows_html = ""
    for _, rad in df.iterrows():
        yoy_klass = "positive" if rad['YoY_diff'] > 0 else "negative" if rad['YoY_diff'] < 0 else "neutral"
        mom_klass = "positive" if rad['MoM_diff'] > 0 else "negative" if rad['MoM_diff'] < 0 else "neutral"
        
        rows_html += f"""
        <tr>
            <td>{rad[dimension_namn]}</td>
            <td style="text-align: right;">{int(rad['Nya kunder']):,}</td>
            <td style="text-align: right;" class="{yoy_klass}">{rad['YoY%']:+.1f}%</td>
            <td style="text-align: right;" class="{mom_klass}">{rad['MoM%']:+.1f}%</td>
        </tr>
        """
    
    return f"""
    <div class="table-container">
        <h3 class="table-title">{titel}</h3>
        <table>
            <thead>
                <tr>
                    <th>{dimension_namn}</th>
                    <th style="text-align: right;">Antal</th>
                    <th style="text-align: right;">YoY%</th>
                    <th style="text-align: right;">MoM%</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """


def generera_tabell_kundstock(titel, df, dimension_namn, max_rader=10):
    """Generera HTML-tabell för kundstock."""
    
    if len(df) == 0:
        return f"""
        <div class="table-container">
            <h3 class="table-title">{titel}</h3>
            <p style="text-align: center; color: #6B7280; padding: 2rem;">Ingen data tillgänglig</p>
        </div>
        """
    
    df = df.head(max_rader)
    
    rows_html = ""
    for _, rad in df.iterrows():
        yoy_klass = "positive" if rad['YoY_diff'] > 0 else "negative" if rad['YoY_diff'] < 0 else "neutral"
        mom_klass = "positive" if rad['MoM_diff'] > 0 else "negative" if rad['MoM_diff'] < 0 else "neutral"
        
        rows_html += f"""
        <tr>
            <td>{rad[dimension_namn]}</td>
            <td style="text-align: right;">{int(rad['Antal kunder']):,}</td>
            <td style="text-align: right;" class="{yoy_klass}">{int(rad['YoY_diff']):+,}</td>
            <td style="text-align: right;" class="{mom_klass}">{int(rad['MoM_diff']):+,}</td>
        </tr>
        """
    
    return f"""
    <div class="table-container">
        <h3 class="table-title">{titel}</h3>
        <table>
            <thead>
                <tr>
                    <th>{dimension_namn}</th>
                    <th style="text-align: right;">Kundstock</th>
                    <th style="text-align: right;">YoY diff</th>
                    <th style="text-align: right;">MoM diff</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """


def generera_innehåll_nya_kunder(df_nya, df_mål, månad, år, kanal='alla'):
    """Generera innehåll för NYA KUNDER vy."""
    
    # Filtrera på månad
    nya_aktuell = filtrera_period(df_nya, år, månad)
    nya_yoy = filtrera_period(df_nya, år - 1, månad)
    nya_mom = filtrera_period(df_nya, år - 1 if månad == 1 else år, 12 if månad == 1 else månad - 1)
    
    # Filtrera på kanal
    nya_aktuell = filtrera_kanal(nya_aktuell, kanal)
    nya_yoy = filtrera_kanal(nya_yoy, kanal)
    nya_mom = filtrera_kanal(nya_mom, kanal)
    
    # KPI
    kpi_nya_aktuell = beräkna_nya_kunder_kpi(nya_aktuell)
    kpi_nya_yoy = beräkna_nya_kunder_kpi(nya_yoy)
    kpi_nya_mom = beräkna_nya_kunder_kpi(nya_mom)
    
    jmf_yoy = jämför_perioder(kpi_nya_aktuell, kpi_nya_yoy)
    jmf_mom = jämför_perioder(kpi_nya_aktuell, kpi_nya_mom)
    
    # Hämta mål för denna månad och kanal
    mål_värde = None
    if df_mål is not None:
        mål_rad = df_mål[(df_mål['Månad'] == månad) & (df_mål['Kanal'] == kanal)]
        if not mål_rad.empty:
            mål_värde = int(mål_rad.iloc[0]['Mål'])
    
    # KPI-kort - endast totalen
    kpi_html = f"""
        <div class="kpi-grid">
            {generera_kpi_card_kombinerad("Nya kunder", 
                kpi_nya_aktuell['Nya kunder'], kpi_nya_yoy['Nya kunder'], kpi_nya_mom['Nya kunder'],
                jmf_yoy['Nya kunder']['Förändring'], jmf_mom['Nya kunder']['Förändring'],
                jmf_yoy['Nya kunder']['Förändring%'], jmf_mom['Nya kunder']['Förändring%'],
                månad=månad, år=år, mål=mål_värde)}
        </div>
    """
    
    # Tabeller för alla dimensioner
    kanal_analys = analysera_dimension_nya_kunder(nya_aktuell, nya_yoy, nya_mom, 'Anskaffningskanal', top_n=6)
    kundtyp_analys = analysera_dimension_nya_kunder(nya_aktuell, nya_yoy, nya_mom, 'KundTyp', top_n=8)
    anstallda_analys = analysera_dimension_nya_kunder(nya_aktuell, nya_yoy, nya_mom, 'Antal anställda', top_n=8)
    sni_analys = analysera_dimension_nya_kunder(nya_aktuell, nya_yoy, nya_mom, 'SNI', top_n=10)
    bolagsform_analys = analysera_dimension_nya_kunder(nya_aktuell, nya_yoy, nya_mom, 'Bolagform', top_n=6)
    omsattning_analys = analysera_dimension_nya_kunder(nya_aktuell, nya_yoy, nya_mom, 'Omsättningsintervall', top_n=8)
    
    if kanal == 'alla':
        # Visa alla tabeller inklusive kanalfördelning
        tabeller_html = f"""
            <div class="tables-grid">
                {generera_tabell_nya_kunder("Anskaffningskanal", kanal_analys, 'Anskaffningskanal', 6)}
                {generera_tabell_nya_kunder("Kundtyp", kundtyp_analys, 'KundTyp', 8)}
                {generera_tabell_nya_kunder("Antal Anställda", anstallda_analys, 'Antal anställda', 8)}
                {generera_tabell_nya_kunder("SNI-kod (Bransch)", sni_analys, 'SNI', 10)}
                {generera_tabell_nya_kunder("Bolagsform", bolagsform_analys, 'Bolagform', 6)}
                {generera_tabell_nya_kunder("Omsättningsintervall", omsattning_analys, 'Omsättningsintervall', 8)}
            </div>
        """
    else:
        # Om en kanal är vald, visa breakdown per andra dimensioner (utan kanal)
        tabeller_html = f"""
            <div class="tables-grid">
                {generera_tabell_nya_kunder("Kundtyp", kundtyp_analys, 'KundTyp', 8)}
                {generera_tabell_nya_kunder("Antal Anställda", anstallda_analys, 'Antal anställda', 8)}
                {generera_tabell_nya_kunder("SNI-kod (Bransch)", sni_analys, 'SNI', 10)}
                {generera_tabell_nya_kunder("Bolagsform", bolagsform_analys, 'Bolagform', 6)}
                {generera_tabell_nya_kunder("Omsättningsintervall", omsattning_analys, 'Omsättningsintervall', 8)}
            </div>
        """
    
    return kpi_html, tabeller_html


def generera_innehåll_netto(df_stock, månad, år):
    """Generera innehåll för NETTOFÖRÄNDRING vy."""
    
    # Kundstock
    stock_aktuell = filtrera_period(df_stock, år, månad)
    stock_yoy = filtrera_period(df_stock, år - 1, månad)
    stock_mom = filtrera_period(df_stock, år - 1 if månad == 1 else år, 12 if månad == 1 else månad - 1)
    
    # KPI
    kpi_stock_aktuell = beräkna_kundstock_kpi(stock_aktuell)
    kpi_stock_yoy = beräkna_kundstock_kpi(stock_yoy)
    kpi_stock_mom = beräkna_kundstock_kpi(stock_mom)
    
    jmf_yoy = jämför_perioder(kpi_stock_aktuell, kpi_stock_yoy)
    jmf_mom = jämför_perioder(kpi_stock_aktuell, kpi_stock_mom)
    
    # KPI-kort
    kpi_html = f"""
        <div class="kpi-grid">
            {generera_kpi_card_kombinerad("Total kundstock", 
                kpi_stock_aktuell['Total kundstock'], kpi_stock_yoy['Total kundstock'], kpi_stock_mom['Total kundstock'],
                jmf_yoy['Total kundstock']['Förändring'], jmf_mom['Total kundstock']['Förändring'],
                jmf_yoy['Total kundstock']['Förändring%'], jmf_mom['Total kundstock']['Förändring%'],
                månad=månad, år=år)}
        </div>
    """
    
    # Tabeller per dimension
    kundtyp = analysera_dimension_kundstock(stock_aktuell, stock_yoy, stock_mom, 'KundTyp', top_n=8)
    anstallda = analysera_dimension_kundstock(stock_aktuell, stock_yoy, stock_mom, 'Antal anställda', top_n=8)
    sni = analysera_dimension_kundstock(stock_aktuell, stock_yoy, stock_mom, 'SNI', top_n=10)
    bolagsform = analysera_dimension_kundstock(stock_aktuell, stock_yoy, stock_mom, 'Bolagform', top_n=6)
    omsattning = analysera_dimension_kundstock(stock_aktuell, stock_yoy, stock_mom, 'Omsättningsintervall', top_n=8)
    
    tabeller_html = f"""
        <div class="tables-grid">
            {generera_tabell_kundstock("Kundtyp", kundtyp, 'KundTyp', 8)}
            {generera_tabell_kundstock("Antal Anställda", anstallda, 'Antal anställda', 8)}
            {generera_tabell_kundstock("SNI-kod (Bransch)", sni, 'SNI', 10)}
            {generera_tabell_kundstock("Bolagsform", bolagsform, 'Bolagform', 6)}
            {generera_tabell_kundstock("Omsättningsintervall", omsattning, 'Omsättningsintervall', 8)}
        </div>
    """
    
    return kpi_html, tabeller_html


# Fortsättning följer i nästa del...
print("Script loaded, generating dashboard...")


def generera_dashboard():
    """Huvudfunktion för att generera dashboard."""
    
    # Hitta filer
    nya_kunder_fil = Path(__file__).parent / "3726d67f-37f5-4502-8e8d-c191ed5167cc - Sheet1.csv"
    kundstock_2024_fil = Path(__file__).parent / "2024-kundstock - Sheet1.csv"
    kundstock_2025_fil = Path(__file__).parent / "2025 kundstock - Sheet1.csv"
    kundmål_fil = Path(__file__).parent / "kundmål - Sheet1.csv"
    
    # Ladda data
    df_nya = ladda_nya_kunder_data(nya_kunder_fil)
    df_stock = ladda_kundstock_data(kundstock_2024_fil, kundstock_2025_fil)
    df_mål = ladda_kundmål_data(kundmål_fil)
    
    # Definiera månader
    månader = [
        (1, "Januari"), (2, "Februari"), (3, "Mars"), (4, "April"),
        (5, "Maj"), (6, "Juni"), (7, "Juli"), (8, "Augusti"),
        (9, "September"), (10, "Oktober")
    ]
    
    # Definiera kanaler
    kanaler = [
        ('alla', 'Alla kanaler'),
        ('fortnox.se', 'Fortnox.Se'),
        ('fortnox', 'Fortnox (Säljare)'),
        ('winback', 'Winback'),
        ('byrå', 'Byrå'),
        ('övrigt', 'Övrigt')
    ]
    
    # Generera innehåll för alla månader, vyer och kanaler
    innehåll_map = {}
    
    for månad_nr, månad_namn in månader:
        # NYA KUNDER vy - för alla kanaler
        for kanal_id, kanal_namn in kanaler:
            kpi, tab = generera_innehåll_nya_kunder(df_nya, df_mål, månad_nr, 2025, kanal_id)
            key = f"nya_{månad_nr}_{kanal_id}"
            innehåll_map[key] = {'kpi': kpi, 'tabeller': tab, 'månad': månad_namn, 'kanal': kanal_namn}
        
        # NETTO vy - ingen kanalfiltrering
        kpi, tab = generera_innehåll_netto(df_stock, månad_nr, 2025)
        key = f"netto_{månad_nr}"
        innehåll_map[key] = {'kpi': kpi, 'tabeller': tab, 'månad': månad_namn}
    
    print(f"Generated {len(innehåll_map)} content combinations")
    
    # Bygg HTML dynamiskt
    kpi_sections = ""
    table_sections = ""
    
    # Nya kunder - alla kombinationer av månad och kanal
    for månad_nr, månad_namn in månader:
        for kanal_id, kanal_namn in kanaler:
            key = f"nya_{månad_nr}_{kanal_id}"
            data = innehåll_map[key]
            display = "block" if månad_nr == 10 and kanal_id == "alla" else "none"
            
            kpi_sections += f'''
        <div class="section" data-view="nya" data-month="{månad_nr}" data-channel="{kanal_id}" style="display: {display};">
            <div class="section-header">
                <h2>Nya kunder - {månad_namn} 2025</h2>
                <p class="subtitle">{kanal_namn}</p>
            </div>
            {data['kpi']}
        </div>
        '''
            
            table_sections += f'''
        <div class="section" data-view="nya" data-month="{månad_nr}" data-channel="{kanal_id}" style="display: {display};">
            {data['tabeller']}
        </div>
        '''
    
    # Nettoförändring - bara månad (ingen kanal)
    for månad_nr, månad_namn in månader:
        key = f"netto_{månad_nr}"
        data = innehåll_map[key]
        display = "none"  # Default dold
        
        kpi_sections += f'''
        <div class="section" data-view="netto" data-month="{månad_nr}" style="display: {display};">
            <div class="section-header">
                <h2>Nettoförändring - {månad_namn} 2025</h2>
                <p class="subtitle">Kundstocksutveckling</p>
            </div>
            {data['kpi']}
        </div>
        '''
        
        table_sections += f'''
        <div class="section" data-view="netto" data-month="{månad_nr}" style="display: {display};">
            {data['tabeller']}
        </div>
        '''
    
    # Nu resten av HTML (CSS kommer från tidigare script - vi kopierar det)
    html = f'''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
    <title>Kundflödesrapport 2025 - Fortnox</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --fortnox-green: #00B888;
            --fortnox-navy: #0A2540;
            --fortnox-gray: #6B7280;
            --fortnox-light-gray: #F3F4F6;
            --fortnox-border: #E5E7EB;
            --color-positive: #10B981;
            --color-negative: #EF4444;
            --color-neutral: #6B7280;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: var(--fortnox-navy);
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
        .header {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: var(--shadow-md); margin-bottom: 2rem; border-left: 6px solid var(--fortnox-green); }}
        .header h1 {{ font-size: 2.5rem; font-weight: 700; color: var(--fortnox-navy); margin-bottom: 0.5rem; }}
        .header-meta {{ color: var(--fortnox-gray); font-size: 0.95rem; }}
        .filter-section {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: var(--shadow-md); margin-bottom: 2rem; text-align: center; }}
        .filter-label {{ color: var(--fortnox-navy); font-weight: 600; font-size: 0.95rem; margin-bottom: 1rem; display: block; }}
        .filter-buttons {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }}
        .filter-button {{ padding: 0.75rem 2rem; border: 2px solid var(--fortnox-border); background: white; color: var(--fortnox-navy); border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; font-family: system-ui, -apple-system, sans-serif; transition: all 0.3s ease; }}
        .filter-button:hover {{ border-color: var(--fortnox-green); color: var(--fortnox-green); }}
        .filter-button.active {{ background: var(--fortnox-green); color: white; border-color: var(--fortnox-green); }}
        .section {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: var(--shadow-md); margin-bottom: 2rem; }}
        .section-header {{ margin-bottom: 2rem; }}
        .section-header h2 {{ font-size: 1.75rem; font-weight: 700; color: var(--fortnox-navy); margin-bottom: 0.5rem; }}
        .subtitle {{ color: var(--fortnox-gray); font-size: 0.95rem; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
        .kpi-card {{ background: linear-gradient(135deg, var(--fortnox-navy) 0%, #0D3A5F 100%); padding: 1.5rem; border-radius: 12px; color: white; }}
        .kpi-title {{ font-size: 0.9rem; font-weight: 600; opacity: 0.9; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .kpi-value {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; }}
        .kpi-comparisons {{ display: flex; flex-direction: column; gap: 0.75rem; }}
        .comparison-row {{ display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem; }}
        .comparison-label {{ font-weight: 600; opacity: 0.8; }}
        .comparison-value {{ opacity: 0.9; }}
        .kpi-change-inline {{ font-weight: 600; display: flex; align-items: center; gap: 0.25rem; }}
        .kpi-change-inline.positive {{ color: var(--color-positive); }}
        .kpi-change-inline.negative {{ color: var(--color-negative); }}
        .kpi-change-inline.neutral {{ color: var(--color-neutral); }}
        .arrow-small {{ font-size: 1rem; }}
        .tables-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 1.5rem; }}
        .table-container {{ background: var(--fortnox-light-gray); padding: 1.5rem; border-radius: 8px; }}
        .table-title {{ font-size: 1.1rem; font-weight: 600; color: var(--fortnox-navy); margin-bottom: 1rem; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; table-layout: fixed; }}
        th, td {{ padding: 0.9rem 1.2rem; text-align: left; vertical-align: middle; }}
        th {{ background: var(--fortnox-navy); color: white; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }}
        td:first-child {{ word-break: break-word; max-width: 0; }}
        td:not(:first-child) {{ white-space: nowrap; }}
        tbody tr {{ border-bottom: 1px solid var(--fortnox-border); }}
        tbody tr:last-child {{ border-bottom: none; }}
        tbody tr:hover {{ background: var(--fortnox-light-gray); }}
        .positive {{ color: var(--color-positive); font-weight: 600; }}
        .negative {{ color: var(--color-negative); font-weight: 600; }}
        .neutral {{ color: var(--color-neutral); }}
        .footer {{ text-align: center; padding: 2rem; color: var(--fortnox-gray); font-size: 0.9rem; }}
        #channel-filter {{ display: block; }}
        .nav-button {{ display: inline-block; margin-top: 1rem; padding: 0.75rem 1.5rem; background: var(--fortnox-navy); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; box-shadow: var(--shadow-md); }}
        .nav-button:hover {{ background: var(--fortnox-green); transform: translateY(-2px); box-shadow: var(--shadow-lg); }}
        
        /* Lösenordsskydd styling */
        .login-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0A2540 0%, #00B888 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}
        
        .login-box {{
            background: white;
            padding: 3rem;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 90%;
            text-align: center;
        }}
        
        .login-box h2 {{
            color: var(--fortnox-navy);
            margin-bottom: 0.5rem;
            font-size: 1.75rem;
        }}
        
        .login-box p {{
            color: var(--fortnox-gray);
            margin-bottom: 2rem;
            font-size: 0.95rem;
        }}
        
        .login-input {{
            width: 100%;
            padding: 1rem;
            border: 2px solid var(--fortnox-border);
            border-radius: 8px;
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            margin-bottom: 1rem;
            transition: border-color 0.3s ease;
        }}
        
        .login-input:focus {{
            outline: none;
            border-color: var(--fortnox-green);
        }}
        
        .login-button {{
            width: 100%;
            padding: 1rem;
            background: var(--fortnox-green);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            transition: background 0.3s ease;
        }}
        
        .login-button:hover {{
            background: #009670;
        }}
        
        .login-error {{
            color: var(--color-negative);
            margin-top: 1rem;
            font-size: 0.9rem;
            display: none;
        }}
        
        .content-hidden {{
            display: none;
        }}
    </style>
    <script>
        // Lösenordsskydd
        const CORRECT_PASSWORD = 'fortnoxftw2025';
        
        function checkPassword() {{
            const input = document.getElementById('passwordInput');
            const error = document.getElementById('loginError');
            const overlay = document.getElementById('loginOverlay');
            const content = document.getElementById('mainContent');
            
            if (input.value === CORRECT_PASSWORD) {{
                overlay.style.display = 'none';
                content.classList.remove('content-hidden');
                // Spara i sessionStorage så användaren inte behöver logga in igen under sessionen
                sessionStorage.setItem('authenticated', 'true');
            }} else {{
                error.style.display = 'block';
                input.value = '';
                input.focus();
            }}
        }}
        
        // Kolla om användaren redan är autentiserad
        window.addEventListener('DOMContentLoaded', function() {{
            if (sessionStorage.getItem('authenticated') === 'true') {{
                document.getElementById('loginOverlay').style.display = 'none';
                document.getElementById('mainContent').classList.remove('content-hidden');
            }}
        }});
        
        // Tillåt Enter-tangent för att logga in
        document.addEventListener('DOMContentLoaded', function() {{
            const input = document.getElementById('passwordInput');
            if (input) {{
                input.addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        checkPassword();
                    }}
                }});
            }}
        }});
    </script>
</head>
<body>
    <!-- Lösenordsskydd overlay -->
    <div id="loginOverlay" class="login-overlay">
        <div class="login-box">
            <h2>🔒 Skyddad Rapport</h2>
            <p>Ange lösenord för att visa kundflödesrapporten</p>
            <input 
                type="password" 
                id="passwordInput" 
                class="login-input" 
                placeholder="Ange lösenord"
                autocomplete="off"
            >
            <button class="login-button" onclick="checkPassword()">Lås upp</button>
            <div id="loginError" class="login-error">❌ Felaktigt lösenord. Försök igen.</div>
        </div>
    </div>
    
    <!-- Huvudinnehåll (dolt tills rätt lösenord anges) -->
    <div id="mainContent" class="content-hidden">
    <div class="container">
        <div class="header">
            <h1>👥 Kundflödesrapport 2025</h1>
            <div class="header-meta">
                Genererad: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
                <span id="current-period">Oktober 2025</span>
            </div>
            <a href="oktober_dashboard.html" class="nav-button">📊 Gå till Nykundsförsäljning →</a>
        </div>
        
        <!-- Månadsfilter -->
        <div class="filter-section">
            <span class="filter-label">Välj månad:</span>
            <div class="filter-buttons">
                <button class="filter-button" onclick="switchMonth(1)" data-month="1">Januari</button>
                <button class="filter-button" onclick="switchMonth(2)" data-month="2">Februari</button>
                <button class="filter-button" onclick="switchMonth(3)" data-month="3">Mars</button>
                <button class="filter-button" onclick="switchMonth(4)" data-month="4">April</button>
                <button class="filter-button" onclick="switchMonth(5)" data-month="5">Maj</button>
                <button class="filter-button" onclick="switchMonth(6)" data-month="6">Juni</button>
                <button class="filter-button" onclick="switchMonth(7)" data-month="7">Juli</button>
                <button class="filter-button" onclick="switchMonth(8)" data-month="8">Augusti</button>
                <button class="filter-button" onclick="switchMonth(9)" data-month="9">September</button>
                <button class="filter-button active" onclick="switchMonth(10)" data-month="10">Oktober</button>
            </div>
        </div>
        
        <!-- Vy-val: Nya kunder / Nettoförändring -->
        <div class="filter-section">
            <span class="filter-label">Visa:</span>
            <div class="filter-buttons">
                <button class="filter-button active" onclick="switchView('nya')" data-view="nya">📈 Nya kunder</button>
                <button class="filter-button" onclick="switchView('netto')" data-view="netto">📊 Nettoförändring</button>
            </div>
        </div>
        
        <!-- Kanalfilter (endast synlig för "Nya kunder") -->
        <div class="filter-section" id="channel-filter">
            <span class="filter-label">Filtrera på anskaffningskanal:</span>
            <div class="filter-buttons">
                <button class="filter-button active" onclick="switchChannel('alla')" data-channel="alla">📊 Alla kanaler</button>
                <button class="filter-button" onclick="switchChannel('fortnox.se')" data-channel="fortnox.se">🌐 Fortnox.Se</button>
                <button class="filter-button" onclick="switchChannel('fortnox')" data-channel="fortnox">👤 Fortnox (Säljare)</button>
                <button class="filter-button" onclick="switchChannel('winback')" data-channel="winback">🔄 Winback</button>
                <button class="filter-button" onclick="switchChannel('byrå')" data-channel="byrå">🏢 Byrå</button>
                <button class="filter-button" onclick="switchChannel('övrigt')" data-channel="övrigt">📦 Övrigt</button>
            </div>
        </div>
        
        <!-- KPI-sektioner -->
        {kpi_sections}
        
        <!-- Tabell-sektioner -->
        {table_sections}
        
        <div class="footer">
            <p>Rapport genererad med Fortnox Analytics Tool</p>
            <p>© {datetime.now().year} Fortnox AB. Alla rättigheter förbehållna.</p>
        </div>
    </div>
    
    <script>
        let currentMonth = 10;
        let currentView = 'nya';
        let currentChannel = 'alla';
        
        const monthNames = {{
            1: 'Januari', 2: 'Februari', 3: 'Mars', 4: 'April',
            5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'Augusti',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'
        }};
        
        function updatePeriodText() {{
            document.getElementById('current-period').textContent = monthNames[currentMonth] + ' 2025';
        }}
        
        function switchMonth(month) {{
            currentMonth = month;
            document.querySelectorAll('[data-month][onclick*="switchMonth"]').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.querySelector(`[data-month="${{month}}"][onclick*="switchMonth"]`).classList.add('active');
            updatePeriodText();
            showContent();
        }}
        
        function switchView(view) {{
            currentView = view;
            document.querySelectorAll('[data-view][onclick*="switchView"]').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.querySelector(`[data-view="${{view}}"][onclick*="switchView"]`).classList.add('active');
            
            // Visa/dölj kanalfilter
            const channelFilter = document.getElementById('channel-filter');
            if (view === 'nya') {{
                channelFilter.style.display = 'block';
            }} else {{
                channelFilter.style.display = 'none';
            }}
            
            showContent();
        }}
        
        function switchChannel(channel) {{
            currentChannel = channel;
            document.querySelectorAll('[data-channel][onclick*="switchChannel"]').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.querySelector(`[data-channel="${{channel}}"][onclick*="switchChannel"]`).classList.add('active');
            showContent();
        }}
        
        function showContent() {{
            // Dölj alla content-sektioner (inte knappar!)
            document.querySelectorAll('.section[data-view]').forEach(section => {{
                section.style.display = 'none';
            }});
            
            // Visa baserat på vy
            if (currentView === 'nya') {{
                // Visa för vald månad och kanal
                document.querySelectorAll(`.section[data-view="nya"][data-month="${{currentMonth}}"][data-channel="${{currentChannel}}"]`).forEach(section => {{
                    section.style.display = 'block';
                }});
            }} else {{
                // Visa för vald månad (ingen kanal)
                document.querySelectorAll(`.section[data-view="netto"][data-month="${{currentMonth}}"]`).forEach(section => {{
                    section.style.display = 'block';
                }});
            }}
        }}
        
        // Initiera
        showContent();
    </script>
    </div>
    </div>
</body>
</html>'''
    
    # Spara filen
    output_fil = Path(__file__).parent / "kundflode_dashboard.html"
    with open(output_fil, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Kundflödes-dashboard genererad framgångsrikt!")
    print(f"📄 Fil: {output_fil}")
    print(f"\n🌐 Öppna filen i din webbläsare för att se dashboarden.")
    
    return output_fil


if __name__ == "__main__":
    generera_dashboard()
